# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

try:
    import simplejson as json
except ImportError:
    import json

import io
import logging
import mock
import mongomock
import os
import pymongo.errors
import shutil
import tempfile
import types
import unittest

import models.build as mbuild
import models.job as mjob
import utils.build


class TestBuildUtils(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.db = mongomock.Database(mongomock.Connection(), "kernel-ci")

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_import_with_dot_name(self):
        json_obj = {
            "job": ".job",
            "kernel": ".kernel"
        }
        job_id, errors = utils.build.import_multiple_builds(
            json_obj, {}, base_path=utils.BASE_PATH)

        self.assertIsNone(job_id)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    @mock.patch("utils.db.get_db_connection")
    def test_import_with_connection_error(self, mock_conn):
        mock_conn.side_effect = pymongo.errors.ConnectionFailure("ConnErr")
        json_obj = {
            "job": "job",
            "kernel": "kernel"
        }

        job_id, errors = utils.build.import_multiple_builds(json_obj, {})
        self.assertIsNone(job_id)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    @mock.patch("utils.build._import_builds")
    @mock.patch("utils.db.get_db_connection")
    def test_import_multiple_builds_connection_error(
            self, mock_conn, mock_import):
        mock_import.return_value = (["docs"], "job-id", {400: ["error"]})
        mock_conn.side_effect = pymongo.errors.ConnectionFailure("ConnErr")
        json_obj = {
            "job": "job",
            "kernel": "kernel"
        }

        _, errors = utils.build.import_multiple_builds(json_obj, {})
        self.assertIsNotNone(errors)
        self.assertListEqual([400, 500], errors.keys())

    @mock.patch("utils.db.save_all")
    @mock.patch("utils.build._import_builds")
    @mock.patch("utils.db.get_db_connection")
    def test_import_multiple_builds_save_error(
            self, mock_conn, mock_import, mock_save):
        mock_conn = self.db
        mock_import.return_value = (["docs"], "job-id", {500: ["error"]})
        mock_save.return_value = (500, None)

        json_obj = {
            "job": "job",
            "kernel": "kernel"
        }

        _, errors = utils.build.import_multiple_builds(json_obj, {})
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    @mock.patch("utils.db.save_all")
    @mock.patch("utils.build._import_builds")
    @mock.patch("utils.db.get_db_connection")
    def test_import_multiple_builds_no_save_error(
            self, mock_conn, mock_import, mock_save):
        mock_conn = self.db
        mock_import.return_value = (["docs"], "job-id", {})
        mock_save.return_value = (201, None)

        json_obj = {
            "job": "job",
            "kernel": "kernel"
        }

        _, errors = utils.build.import_multiple_builds(json_obj, {})
        self.assertDictEqual({}, errors)

    def test_traverse_buld_dir_with_ioerror(self):
        try:
            errors = {}
            temp_dir = tempfile.mkdtemp()
            build_dir = os.path.join(temp_dir, "build_dir")
            os.mkdir(build_dir)
            io.open(os.path.join(build_dir, "build.json"), mode="w")

            patcher = mock.patch("io.open")
            mock_open = patcher.start()
            mock_open.side_effect = IOError("IOError")
            self.addCleanup(patcher.stop)

            build_doc = utils.build._traverse_build_dir(
                "build_dir",
                temp_dir, "job", "kernel", "job_id", "job_date", errors, {})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertIsNotNone(errors)
        self.assertIsNone(build_doc)
        self.assertListEqual([500], errors.keys())

    def test_traverse_buld_dir_with_jsonerror(self):
        try:
            errors = {}
            temp_dir = tempfile.mkdtemp()
            build_dir = os.path.join(temp_dir, "build_dir")
            os.mkdir(build_dir)
            with io.open(os.path.join(build_dir, "build.json"), mode="w") as f:
                f.write(u"a string of text")

            build_doc = utils.build._traverse_build_dir(
                "build_dir",
                temp_dir, "job", "kernel", "job_id", "job_date", errors, {})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertIsNotNone(errors)
        self.assertIsNone(build_doc)
        self.assertListEqual([500], errors.keys())

    def test_traverse_build_dir_with_valid_data(self):
        build_data = {
            "arch": "arm",
            "git_url": "git://git.example.org",
            "git_branch": "test/branch",
            "git_describe": "vfoo.bar",
            "git_commit": "1234567890",
            "defconfig": "defoo_confbar",
            "kernel_image": "zImage",
            "kernel_config": "kernel.config",
            "modules_dir": "foo/bar",
            "build_log": "file.log"
        }

        try:
            errors = {}
            temp_dir = tempfile.mkdtemp()
            build_dir = os.path.join(temp_dir, "build_dir")
            os.mkdir(build_dir)
            with io.open(os.path.join(build_dir, "build.json"), mode="w") as f:
                f.write(json.dumps(build_data, ensure_ascii=False))

            build_doc = utils.build._traverse_build_dir(
                "build_dir",
                temp_dir, "job", "kernel", "job_id", "job_date", errors, {})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual("job", build_doc.job)
        self.assertEqual("kernel", build_doc.kernel)

    def test_parse_build_data_no_dict(self):
        build_data = []
        errors = {}

        build_doc = utils.build.parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsNone(build_doc)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    def test_parse_build_data_missing_key(self):
        build_data = {"arch": "arm"}
        errors = {}

        build_doc = utils.build.parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsNone(build_doc)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    def test_parse_build_data_no_version(self):
        build_data = {"defconfig": "defconfig"}
        errors = {}

        build_doc = utils.build.parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual(build_doc.version, "1.0")

    def test_parse_build_data_version(self):
        build_data = {
            "defconfig": "defconfig",
            "version": "foo"
        }
        errors = {}

        build_doc = utils.build.parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual(build_doc.version, "foo")

    def test_parse_build_data_errors_warnings(self):
        build_data = {
            "defconfig": "defconfig",
            "build_errors": 3,
            "build_warnings": 1
        }
        errors = {}

        build_doc = utils.build.parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual(build_doc.errors, 3)
        self.assertEqual(build_doc.warnings, 1)

    def test_parse_build_data_no_job_no_kernel(self):
        build_data = {"defconfig": "defconfig"}
        errors = {}

        build_doc = utils.build.parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual(build_doc.job, "job")
        self.assertEqual(build_doc.kernel, "kernel")

    def test_parse_build_data_no_defconfig_full(self):
        build_data = {"defconfig": "defconfig"}
        errors = {}

        build_doc = utils.build.parse_build_data(
            build_data, "job", "kernel", errors)

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual(build_doc.defconfig_full, "defconfig")

    def test_parse_build_data_diff_fragments(self):
        build_data = {
            "arch": "arm",
            "defconfig": "defoo_confbar",
            "job": "job",
            "kernel": "kernel",
            "kconfig_fragments": "frag-CONFIG_TEST=y.config"
        }

        build_doc = utils.build.parse_build_data(
            build_data, "job", "kernel", {}, "arm-build_dir")

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual(
            build_doc.defconfig_full, "defoo_confbar+CONFIG_TEST=y")
        self.assertEqual(build_doc.defconfig, "defoo_confbar")

    def test_parse_build_metadata(self):
        build_data = {
            "arch": "arm",
            "git_url": "git://git.example.org",
            "git_branch": "test/branch",
            "git_describe": "vfoo.bar",
            "git_commit": "1234567890",
            "defconfig": "defoo_confbar",
            "kernel_image": "zImage",
            "kernel_config": "kernel.config",
            "dtb_dir": "dtbs",
            "modules_dir": "foo/bar",
            "build_log": "file.log",
            "kconfig_fragments": "fragment",
            "compiler_version": "gcc",
            "cross_compile": "foo"
        }
        build_doc = utils.build.parse_build_data(
            build_data, "job", "kernel", {}, "arm-build_dir")

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertIsInstance(build_doc.metadata, types.DictionaryType)
        self.assertIsInstance(build_doc.dtb_dir_data, types.ListType)
        self.assertNotEqual({}, build_doc.metadata)
        self.assertEqual("gcc", build_doc.metadata["compiler_version"])
        self.assertEqual("foo", build_doc.metadata["cross_compile"])
        self.assertEqual(build_doc.kconfig_fragments, "fragment")
        self.assertEqual(build_doc.arch, "arm")
        self.assertEqual(build_doc.git_commit, "1234567890")
        self.assertEqual(build_doc.git_branch, "test/branch")
        self.assertEqual(build_doc.git_url, "git://git.example.org")
        self.assertEqual(build_doc.defconfig_full, "defoo_confbar")
        self.assertEqual(build_doc.defconfig, "defoo_confbar")
        self.assertEqual(build_doc.build_log, "file.log")
        self.assertEqual(build_doc.modules_dir, "foo/bar")
        self.assertEqual(build_doc.dtb_dir, "dtbs")
        self.assertEqual(build_doc.kernel_config, "kernel.config")
        self.assertEqual(build_doc.kernel_image, "zImage")

    def test_parse_dtb_dir_single_file(self):
        temp_dir = tempfile.mkdtemp()
        expected = ["arm-dtb/arm.dtb"]
        try:
            dtb_dir = os.path.join(temp_dir, "dtbs")
            os.mkdir(dtb_dir)
            arm_dtb_dir = os.path.join(dtb_dir, "arm-dtb")
            arm_dtb_file = os.path.join(arm_dtb_dir, "arm.dtb")
            os.mkdir(arm_dtb_dir)
            io.open(arm_dtb_file, mode="w")

            results = utils.build.parse_dtb_dir(temp_dir, "dtbs")
            self.assertListEqual(expected, results)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_parse_dtb_dir_complex_case(self):
        temp_dir = tempfile.mkdtemp()
        expected = ["a-dtb.dtb", "arm-dtb/arm.dtb"]
        try:
            dtb_dir = os.path.join(temp_dir, "dtbs")
            os.mkdir(dtb_dir)
            os.mkdir(os.path.join(dtb_dir, ".fake-dtb-dir"))
            arm_dtb_dir = os.path.join(dtb_dir, "arm-dtb")
            arm_dtb_file = os.path.join(arm_dtb_dir, "arm.dtb")
            os.mkdir(arm_dtb_dir)
            io.open(arm_dtb_file, mode="w")
            io.open(os.path.join(arm_dtb_dir, ".fake-file.dtb"), mode="w")
            io.open(os.path.join(dtb_dir, "a-dtb.dtb"), mode="w")

            results = utils.build.parse_dtb_dir(temp_dir, "dtbs")
            self.assertListEqual(expected, results)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @mock.patch("utils.build._traverse_build_dir")
    @mock.patch("os.path.exists")
    def test_traverse_kernel_dir_fake(self, mock_exists, mock_trav):
        mock_exists.return_value = True
        mock_trav.side_effect = [None, None, None, "foo"]
        kernel_dir = tempfile.mkdtemp()

        def scan_func(to_scan):
            yield None
            yield None
            yield None
            yield None

        try:
            docs, job_status, errors = utils.build._traverse_kernel_dir(
                kernel_dir,
                "job",
                "kernel", "job_id", "job_date", {}, scan_func=scan_func)
        finally:
            shutil.rmtree(kernel_dir, ignore_errors=True)

        self.assertListEqual(["foo"], docs)
        self.assertEqual("PASS", job_status)
        self.assertDictEqual({}, errors)

    def test_traverse_kernel_dir_building(self):
        kernel_dir = tempfile.mkdtemp()
        try:
            docs, job_status, errors = utils.build._traverse_kernel_dir(
                kernel_dir, "job", "kernel", "job_id", "job_date", {})
        finally:
            shutil.rmtree(kernel_dir, ignore_errors=True)

        self.assertEqual("BUILD", job_status)
        self.assertListEqual([], docs)
        self.assertDictEqual({}, errors)

    def test_traverse_kernel_dir(self):
        kernel_dir = tempfile.mkdtemp()
        build_dir = os.path.join(kernel_dir, "arm-fake_defconfig")
        build_data = {
            "arch": "arm",
            "defconfig": "fake_defconfig",
            "kernel": "kernel",
            "job": "job"
        }
        try:
            os.mkdir(build_dir)
            io.open(os.path.join(kernel_dir, ".done"), mode="w")
            with io.open(os.path.join(build_dir, "build.json"), mode="w") as w:
                w.write(json.dumps(build_data, ensure_ascii=False))

            docs, job_status, errors = utils.build._traverse_kernel_dir(
                kernel_dir, "job", "kernel", "job_id", "job_date", {})
        finally:
            shutil.rmtree(kernel_dir, ignore_errors=True)

        self.assertEqual("PASS", job_status)
        self.assertDictEqual({}, errors)
        self.assertEqual(1, len(docs))
        self.assertEqual("fake_defconfig", docs[0].defconfig)

    def test_update_job_doc(self):
        job_doc = mjob.JobDocument("job", "kernel")
        build_doc = mbuild.BuildDocument(
            "job", "kernel", "defconfig")
        build_doc.git_branch = "local/branch"
        build_doc.git_commit = "1234567890"
        build_doc.git_describe = "kernel.version"
        build_doc.git_url = "git://url.git"

        utils.build._update_job_doc(
            job_doc, "job_id", "PASS", [build_doc], self.db)

        self.assertIsInstance(job_doc, mjob.JobDocument)
        self.assertIsNotNone(job_doc.id)
        self.assertIsNotNone(job_doc.git_branch)
        self.assertIsNotNone(job_doc.git_commit)
        self.assertIsNotNone(job_doc.git_describe)
        self.assertIsNotNone(job_doc.git_url)
        self.assertEqual("job_id", job_doc.id)
        self.assertEqual("local/branch", job_doc.git_branch)
        self.assertEqual("1234567890", job_doc.git_commit)
        self.assertEqual("kernel.version", job_doc.git_describe)
        self.assertEqual("git://url.git", job_doc.git_url)

    def test_update_job_doc_no_defconfig(self):
        job_doc = mjob.JobDocument("job", "kernel")

        utils.build._update_job_doc(
            job_doc, None, "PASS", [], self.db)

        self.assertIsInstance(job_doc, mjob.JobDocument)
        self.assertIsNone(job_doc.id)
        self.assertIsNone(job_doc.git_branch)
        self.assertIsNone(job_doc.git_commit)
        self.assertIsNone(job_doc.git_describe)
        self.assertIsNone(job_doc.git_url)

    def test_update_job_doc_with_job_doc_and_fake(self):
        job_doc = mjob.JobDocument("job", "kernel")
        job_doc_b = mjob.JobDocument("job", "kernel")
        build_doc = mbuild.BuildDocument(
            "job", "kernel", "defconfig")
        build_doc.git_branch = "local/branch"
        build_doc.git_commit = "1234567890"
        build_doc.git_describe = "kernel.version"
        build_doc.git_url = "git://url.git"

        utils.build._update_job_doc(
            job_doc,
            "job_id",
            "PASS", [job_doc_b, {"foo": "bar"}, build_doc], self.db)

        self.assertIsInstance(job_doc, mjob.JobDocument)
        self.assertIsNotNone(job_doc.git_branch)
        self.assertIsNotNone(job_doc.git_commit)
        self.assertIsNotNone(job_doc.git_describe)
        self.assertIsNotNone(job_doc.git_url)
        self.assertEqual("local/branch", job_doc.git_branch)
        self.assertEqual("1234567890", job_doc.git_commit)
        self.assertEqual("kernel.version", job_doc.git_describe)
        self.assertEqual("git://url.git", job_doc.git_url)

    def test_update_job_doc_with_job_doc_fake_and_wrong(self):
        job_doc = mjob.JobDocument("job", "kernel")
        job_doc_b = mjob.JobDocument("job", "kernel")
        build_doc = mbuild.BuildDocument(
            "job", "kernel", "defconfig")
        build_doc.git_branch = "local/branch"
        build_doc.git_commit = "1234567890"
        build_doc.git_describe = "kernel.version"
        build_doc.git_url = "git://url.git"

        build_doc_b = mbuild.BuildDocument(
            "job_b", "kernel_b", "defconfig_b")

        utils.build._update_job_doc(
            job_doc,
            "job_id",
            "PASS",
            [job_doc_b, build_doc_b, {"foo": "bar"}, build_doc],
            self.db
        )

        self.assertIsInstance(job_doc, mjob.JobDocument)
        self.assertIsNotNone(job_doc.git_branch)
        self.assertIsNotNone(job_doc.git_commit)
        self.assertIsNotNone(job_doc.git_describe)
        self.assertIsNotNone(job_doc.git_url)
        self.assertEqual("local/branch", job_doc.git_branch)
        self.assertEqual("1234567890", job_doc.git_commit)
        self.assertEqual("kernel.version", job_doc.git_describe)
        self.assertEqual("git://url.git", job_doc.git_url)

    def test_import_single_build_wrong_name(self):
        json_obj = {
            "job": ".ajob",
            "kernel": "akernel",
            "defconfig": "defconfig",
            "arch": "arch"
        }
        defconfig_id, job_id, errors = utils.build.import_single_build(
            json_obj, {})

        self.assertIsNone(defconfig_id)
        self.assertIsNone(job_id)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    @mock.patch("os.path.isdir")
    def test_import_single_build_no_build_dir(self, mock_dir):
        mock_dir.return_value = False
        json_obj = {
            "job": ".ajob",
            "kernel": "akernel",
            "defconfig": "defconfig",
            "arch": "arch"
        }
        defconfig_id, job_id, errors = utils.build.import_single_build(
            json_obj, {})

        self.assertIsNone(defconfig_id)
        self.assertIsNone(job_id)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    @mock.patch("utils.db.get_db_connection")
    def test_import_single_build_with_connection_error(self, mock_conn):
        mock_conn.side_effect = pymongo.errors.ConnectionFailure("ConnErr")
        json_obj = {
            "job": "ajob",
            "kernel": "akernel",
            "defconfig": "defconfig",
            "arch": "arch"
        }
        defconfig_id, job_id, errors = utils.build.import_single_build(
            json_obj, {})

        self.assertIsNone(defconfig_id)
        self.assertIsNone(job_id)
        self.assertIsNotNone(errors)
        self.assertListEqual([500], errors.keys())

    @mock.patch("utils.db.save")
    @mock.patch("utils.build._update_job_doc")
    @mock.patch("utils.build._traverse_build_dir")
    @mock.patch("utils.db.find_one2")
    @mock.patch("os.path.isdir")
    def test_import_single_build(
            self, mock_dir, mock_find, mock_tr, mock_up, mock_save):
        mock_dir.return_value = True

        job_doc = {"job": "ajob", "kernel": "kernel", "_id": "job_id"}
        build_doc = mbuild.BuildDocument(
            "job", "kernel", "defconfig")

        mock_tr.return_value = build_doc
        mock_find.return_value = job_doc
        mock_up.return_value = 201
        mock_save.return_value = (201, "build_id")

        json_obj = {
            "job": "ajob",
            "kernel": "akernel",
            "defconfig": "defconfig",
            "arch": "arch"
        }
        defconfig_id, job_id, errors = utils.build.import_single_build(
            json_obj, {})

        self.assertDictEqual({}, errors)
        self.assertIsNotNone(defconfig_id)
        self.assertIsNotNone(job_id)
        self.assertEqual("build_id", defconfig_id)
        self.assertEqual("job_id", job_id)
