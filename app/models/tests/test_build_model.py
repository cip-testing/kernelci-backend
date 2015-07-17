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

import unittest

import models.base as modb
import models.build as mbuild


class TestDefconfModel(unittest.TestCase):

    def test_build_document_valid_instance(self):
        build_doc = mbuild.BuildDocument("job", "kernel", "defconfig")
        self.assertIsInstance(build_doc, modb.BaseDocument)
        self.assertIsInstance(build_doc, mbuild.BuildDocument)

    def test_build_document_collection(self):
        build_doc = mbuild.BuildDocument("job", "kernel", "defconfig")
        self.assertEqual(build_doc.collection, "defconfig")

    def test_build_document_to_dict(self):
        build_doc = mbuild.BuildDocument(
            "job", "kernel", "defconfig", "defconfig_full")
        build_doc.id = "defconfig_id"
        build_doc.job_id = "job_id"
        build_doc.created_on = "now"
        build_doc.metadata = {}
        build_doc.status = "FAIL"
        build_doc.dirname = "defconfig"
        build_doc.boot_resul_description = []
        build_doc.errors = 1
        build_doc.warnings = 1
        build_doc.build_time = 1
        build_doc.arch = "foo"
        build_doc.git_url = "git_url"
        build_doc.git_commit = "git_commit"
        build_doc.git_branch = "git_branch"
        build_doc.git_describe = "git_describe"
        build_doc.version = "1.0"
        build_doc.modules = "modules-file"
        build_doc.dtb_dir = "dtb-dir"
        build_doc.dtb_dir_data = ["a-file"]
        build_doc.kernel_config = "kernel-config"
        build_doc.system_map = "system-map"
        build_doc.text_offset = "offset"
        build_doc.kernel_image = "kernel-image"
        build_doc.modules_dir = "modules-dir"
        build_doc.build_log = "build.log"
        build_doc.kconfig_fragments = "config-frag"
        build_doc.file_server_resource = "file-resource"
        build_doc.file_server_url = "server-url"

        expected = {
            "_id": "defconfig_id",
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "job_id": "job_id",
            "created_on": "now",
            "metadata": {},
            "status": "FAIL",
            "defconfig": "defconfig",
            "errors": 1,
            "warnings": 1,
            "build_time": 1,
            "arch": "foo",
            "dirname": "defconfig",
            "git_url": "git_url",
            "git_describe": "git_describe",
            "git_branch": "git_branch",
            "git_commit": "git_commit",
            "build_platform": [],
            "version": "1.0",
            "dtb_dir": "dtb-dir",
            "dtb_dir_data": ["a-file"],
            "kernel_config": "kernel-config",
            "kernel_image": "kernel-image",
            "system_map": "system-map",
            "text_offset": "offset",
            "modules": "modules-file",
            "modules_dir": "modules-dir",
            "build_log": "build.log",
            "kconfig_fragments": "config-frag",
            "defconfig_full": "defconfig_full",
            "file_server_resource": "file-resource",
            "file_server_url": "server-url",
        }

        self.assertDictEqual(expected, build_doc.to_dict())

    def test_deconfig_set_status_wrong_and_right(self):
        build_doc = mbuild.BuildDocument("job", "kernel", "defconfig")

        self.assertRaises(ValueError, setattr, build_doc, "status", "foo")
        self.assertRaises(ValueError, setattr, build_doc, "status", [])
        self.assertRaises(ValueError, setattr, build_doc, "status", {})
        self.assertRaises(ValueError, setattr, build_doc, "status", ())

        build_doc.status = "FAIL"
        self.assertEqual(build_doc.status, "FAIL")
        build_doc.status = "PASS"
        self.assertEqual(build_doc.status, "PASS")
        build_doc.status = "UNKNOWN"
        self.assertEqual(build_doc.status, "UNKNOWN")
        build_doc.status = "BUILD"
        self.assertEqual(build_doc.status, "BUILD")

    def test_defconfig_set_build_platform_wrong(self):
        build_doc = mbuild.BuildDocument("job", "kernel", "defconfig")

        self.assertRaises(
            TypeError, setattr, build_doc, "build_platform", ())
        self.assertRaises(
            TypeError, setattr, build_doc, "build_platform", {})
        self.assertRaises(
            TypeError, setattr, build_doc, "build_platform", "")

    def test_defconfig_set_build_platform(self):
        build_doc = mbuild.BuildDocument("job", "kernel", "defconfig")
        build_doc.build_platform = ["a", "b"]

        self.assertListEqual(build_doc.build_platform, ["a", "b"])

    def test_defconfig_set_metadata_wrong(self):
        build_doc = mbuild.BuildDocument("job", "kernel", "defconfig")

        self.assertRaises(TypeError, setattr, build_doc, "metadata", ())
        self.assertRaises(TypeError, setattr, build_doc, "metadata", [])
        self.assertRaises(TypeError, setattr, build_doc, "metadata", "")

    def test_defconfig_from_json_is_none(self):
        self.assertIsNone(mbuild.BuildDocument.from_json({}))
        self.assertIsNone(mbuild.BuildDocument.from_json(""))
        self.assertIsNone(mbuild.BuildDocument.from_json([]))
        self.assertIsNone(mbuild.BuildDocument.from_json(()))

    def test_defconfog_from_json(self):
        json_obj = {
            "name": "job-kernel-defconfig_full",
            "_id": "defconfig_id",
            "job": "job",
            "kernel": "kernel",
            "defconfig": "defconfig",
            "job_id": "job_id",
            "created_on": "now",
            "metadata": {
                "foo": "bar"
            },
            "status": "FAIL",
            "defconfig": "defconfig",
            "errors": 1,
            "warnings": 1,
            "build_time": 1,
            "arch": "foo",
            "dirname": "defconfig",
            "git_url": "git_url",
            "git_describe": "git_describe",
            "git_branch": "git_branch",
            "git_commit": "git_commit",
            "build_platform": [],
            "version": "1.0",
            "dtb_dir": "dtb-dir",
            "dtb_dir_data": ["a-file"],
            "kernel_config": "kernel-config",
            "kernel_image": "kernel-image",
            "system_map": "system-map",
            "text_offset": "offset",
            "modules": "modules-file",
            "modules_dir": "modules-dir",
            "build_log": "build.log",
            "kconfig_fragments": "config-frag",
            "defconfig_full": "defconfig_full",
            "file_server_resource": "file-resource",
            "file_server_url": "server-url",
        }
        build_doc = mbuild.BuildDocument.from_json(json_obj)

        self.assertIsInstance(build_doc, mbuild.BuildDocument)
        self.assertEqual(build_doc.id, "defconfig_id")
        self.assertEqual(build_doc.defconfig_full, "defconfig_full")
        self.assertEqual(build_doc.version, "1.0")
        self.assertEqual(build_doc.errors, 1)
        self.assertEqual(build_doc.warnings, 1)
        self.assertEqual(build_doc.build_time, 1)
        self.assertListEqual(build_doc.build_platform, [])
        self.assertDictEqual(build_doc.metadata, {"foo": "bar"})
