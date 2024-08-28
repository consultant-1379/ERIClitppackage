from unittest import TestCase

from litp.core.model_manager import ModelManager
from litp.core.plugin_context_api import PluginApiContext
from litp.core.model_type import PropertyType
from litp.core.model_type import ItemType
from litp.core.model_type import Collection
from litp.core.model_type import Property
from litp.core.model_type import Child
from litp.core.model_type import RefCollection
from litp.core.validators import ValidationError
from litp.core.model_item import ModelItem

from package_plugin.package_plugin import PackagePlugin


class MockExecutionManager(object):
    pass


class PackageValidationTest(TestCase):
    def setUp(self):
        self.plugin = PackagePlugin()
        self.model = ModelManager()
        self.api = PluginApiContext(self.model)
        self.execution_manager = MockExecutionManager()
        self.model.register_property_types([
            PropertyType("any_string", regex=r"^.*$")
        ])
        self.model.register_item_types([
            ItemType(
                "root",
                packages=Collection("software-item"),
                node=Child("node")
            ),
            ItemType(
                "node",
                packages=RefCollection("software-item"),
                hostname=Property("any_string", required=True, default="node")
            ),
            ItemType(
                "software-item"
            ),
            ItemType(
                "package",
                extend_item="software-item",
                name=Property("any_string"),
                arch=Property("any_string"),
                version=Property("any_string"),
                repository=Property("any_string"),
                config=Property("any_string"),
                requires=Property("any_string")
            ),
            ItemType(
                "package-list",
                extend_item="software-item",
                name=Property("any_string"),
                packages=Collection("package")
            )
        ])
        self.model.create_root_item("root", "/")
        self.model.create_item("node", "/node")

    def _create_item(self, *args, **kwargs):
        ret = self.model.create_item(*args, **kwargs)
        if not isinstance(ret, ModelItem):
            raise Exception("can't create item: " + str(ret))
        return ret

    def _create_inherited(self, source_vpath, target_vpath):
        ret = self.model.create_inherited(source_vpath, target_vpath)
        if not isinstance(ret, ModelItem):
            raise Exception("can't create inherited item: " + str(ret))
        return ret

    def _remove_item(self, *args, **kwargs):
        ret = self.model.remove_item(*args, **kwargs)
        if not isinstance(ret, ModelItem):
            raise Exception("can't remove item: " + str(ret))
        return ret

    def test_packages(self):
        self._create_item(
            "package", "/packages/p-a1", name="p", arch="a1")
        self._create_item(
            "package", "/packages/p-a2", name="p", arch="a2")

        self._create_inherited("/packages/p-a1", "/node/packages/p1")
        self._create_inherited("/packages/p-a1", "/node/packages/p2")
        self._create_inherited("/packages/p-a1", "/node/packages/p3")

        errors = self.plugin.validate_model(self.api)
        self.assertEquals(3, len(errors))

    def test_packages_with_removal(self):
        self._create_item(
            "package", "/packages/p-a1", name="p", arch="a1")
        self._create_inherited("/packages/p-a1", "/node/packages/p1")

        self.model.set_all_applied()

        self._remove_item("/node/packages/p1")
        self._create_item(
            "package", "/packages/p-a2", name="p", arch="a2")
        self._create_inherited("/packages/p-a2", "/node/packages/p2")

        errors = self.plugin.validate_model(self.api)
        self.assertEquals(0, len(errors))

    def test_packages_and_package_lists(self):
        self._create_item(
            "package-list", "/packages/l1", name="l1")
        self._create_item(
            "package", "/packages/l1/packages/p_a1", name="p", arch="a1")
        self._create_item(
            "package-list", "/packages/l2", name="l2")
        self._create_item(
            "package", "/packages/l2/packages/p_a2", name="p", arch="a2")

        self._create_inherited("/packages/l1/packages/p_a1",
                               "/node/packages/p")
        self._create_inherited("/packages/l2", "/node/packages/l2")

        errors = self.plugin.validate_model(self.api)
        self.assertEquals(2, len(errors))

    def test_package_lists_1(self):
        self._create_item(
            "package-list", "/packages/l", name="l")
        self._create_item(
            "package", "/packages/l/packages/p_a1", name="p", arch="a1")
        self._create_item(
            "package", "/packages/l/packages/p_a2", name="p", arch="a2")

        self._create_inherited("/packages/l", "/node/packages/l")

        errors = self.plugin.validate_model(self.api)
        self.assertEquals(2, len(errors))

    def test_package_lists_2(self):
        self._create_item(
            "package-list", "/packages/l1", name="l1")
        self._create_item(
            "package", "/packages/l1/packages/p", name="p", arch="a1")
        self._create_item(
            "package-list", "/packages/l2", name="l2")
        self._create_item(
            "package", "/packages/l2/packages/p", name="p", arch="a2")

        self._create_inherited("/packages/l1", "/node/packages/l1")
        self._create_inherited("/packages/l2", "/node/packages/l2")

        errors = self.plugin.validate_model(self.api)
        self.assertEquals(2, len(errors))

    def test_requires_initial_state(self):

        # Case 1. package is initial and a package that it requires
        #         is not in the model, or inherited to the node

        package1 = self._create_item(
                "package", "/packages/p1",
                name="pkg1", requires="unmodelled"
            )

        self._create_inherited(
                package1.get_vpath(), "/node/packages/p1")

        errors = self.plugin.validate_model(self.api)

        expected = ValidationError(
                item_path='/node/packages/p1',
                error_message='Package "unmodelled", required by "pkg1",'
                ' is not inherited to this node.'
            )

        self.assertEquals([expected], errors)

    def test_requires_applied_or_update_but_requirement_missing(self):

        # Case 2. package is in updated or applied, but a package that
        #         it requires is missing from the model. If this
        #         situation arises, it is not very good.

        package1 = self._create_item(
                    "package", "/packages/p1", name="pkg1", requires="missing")

        self._create_inherited(
                package1.get_vpath(), "/node/packages/p1")

        self.model.set_all_applied()

        errors = self.plugin.validate_model(self.api)

        expected = ValidationError(
                item_path='/node/packages/p1',
                error_message='Package "missing", required by "pkg1", is not inherited to this node.'
            )

        self.assertEquals([expected], errors)

    def test_requires_try_to_remove_requirement(self):

        # Case 3. package is in updated or applied, need to check
        #         if there is any attempt to remove a package that
        #         this package requires

        package1 = self._create_item(
                    "package", "/packages/p1", name="pkg1")

        self._create_inherited(
                package1.get_vpath(), "/node/packages/p1")

        package2 = self._create_item(
                "package", "/packages/p2",
                name="pkg2", requires="pkg1"
            )

        self._create_inherited(
                package2.get_vpath(), "/node/packages/p2")

        self.model.set_all_applied()

        # removing the p1 required by p2 should give an error
        self._remove_item("/node/packages/p1")

        errors = self.plugin.validate_model(self.api)

        expected = ValidationError(
                item_path='/node/packages/p2',
                error_message='Package "pkg1" is required by "pkg2" and cannot be removed.'
            )

        self.assertEquals([expected], errors)

    def test_requires_for_cycle_level_1(self):

        # level 1 circular dependence  p2 <- p1 <- p2
        p1 = self._create_item(
                "package", "/packages/p1", name="p1", requires="p2")

        p2 = self._create_item(
                "package", "/packages/p2", name="p2", requires="p1")

        self._create_inherited(
                p1.get_vpath(), "/node/packages/p1")

        self._create_inherited(
                p2.get_vpath(), "/node/packages/p2")

        errors = self.plugin.validate_model(self.api)

        self.assertEquals(2, len(errors))

        e1 = ValidationError(
                    error_message='A cyclical requires exists with'
                    ' package(s) "p2" defined by "requires" property',
                    item_path="/node/packages/p1"
                )
        e2 = ValidationError(
                    error_message='A cyclical requires exists with'
                    ' package(s) "p1" defined by "requires" property',
                    item_path="/node/packages/p2"
                )

        self.assertTrue(e1 in errors)
        self.assertTrue(e2 in errors)


    def test_requires_for_cycle_level_2(self):

        # level 2 circular dependence  C <- B <- A <- C
        A = self._create_item(
                "package", "/packages/A", name="A", requires="B")

        B = self._create_item(
                "package", "/packages/B", name="B", requires="C")

        C = self._create_item(
                "package", "/packages/C", name="C", requires="A")

        self._create_inherited(
                A.get_vpath(), "/node/packages/A")

        self._create_inherited(
                B.get_vpath(), "/node/packages/B")

        self._create_inherited(
                C.get_vpath(), "/node/packages/C")

        errors = self.plugin.validate_model(self.api)

        self.assertEquals(3, len(errors))

        e1 = ValidationError(
                    error_message='A cyclical requires exists with'
                    ' package(s) "B" defined by "requires" property',
                    item_path="/node/packages/A"
                )

        e2 = ValidationError(
                    error_message='A cyclical requires exists with'
                    ' package(s) "C" defined by "requires" property',
                    item_path="/node/packages/B"
                )

        e3 = ValidationError(
                    error_message='A cyclical requires exists with'
                    ' package(s) "A" defined by "requires" property',
                    item_path="/node/packages/C"
                )

        self.assertTrue(e1 in errors)
        self.assertTrue(e2 in errors)
        self.assertTrue(e3 in errors)

    def test_requries_for_cycles_complicated(self):

        A = self._create_item(
                "package", "/packages/A", name="A", requires="B")

        B = self._create_item(
                "package", "/packages/B", name="B", requires="C,X")

        C = self._create_item(
                "package", "/packages/C", name="C", requires="A")

        X = self._create_item(
                "package", "/packages/X", name="X", requires="Y")

        Y = self._create_item(
                "package", "/packages/Y", name="Y", requires="B")

        self._create_inherited(
                A.get_vpath(), "/node/packages/A")

        self._create_inherited(
                B.get_vpath(), "/node/packages/B")

        self._create_inherited(
                C.get_vpath(), "/node/packages/C")

        self._create_inherited(
                X.get_vpath(), "/node/packages/X")

        self._create_inherited(
                Y.get_vpath(), "/node/packages/Y")

        errors = self.plugin.validate_model(self.api)


        e1 = ValidationError(
                    error_message='A cyclical requires exists with'
                    ' package(s) "B" defined by "requires" property',
                    item_path="/node/packages/A"
                )

        e2 = ValidationError(
                    error_message='A cyclical requires exists with'
                    ' package(s) "C, X" defined by "requires" property',
                    item_path="/node/packages/B"
                )

        e3 = ValidationError(
                    error_message='A cyclical requires exists with'
                    ' package(s) "A" defined by "requires" property',
                    item_path="/node/packages/C"
                )

        e4 = ValidationError(
                    error_message='A cyclical requires exists with'
                    ' package(s) "Y" defined by "requires" property',
                    item_path="/node/packages/X"
                )

        e5 = ValidationError(
                    error_message='A cyclical requires exists with'
                    ' package(s) "B" defined by "requires" property',
                    item_path="/node/packages/Y"
                )

        self.assertEquals(5, len(errors))
        self.assertTrue(e1 in errors)
        self.assertTrue(e2 in errors)
        self.assertTrue(e3 in errors)
        self.assertTrue(e4 in errors)
        self.assertTrue(e5 in errors)

    def test_requries_for_cycles_complicated_no_cycle(self):

        A = self._create_item(
                "package", "/packages/A", name="A", requires="B")

        B = self._create_item(
                "package", "/packages/B", name="B", requires="C,X")

        C = self._create_item(
                "package", "/packages/C", name="C")

        X = self._create_item(
                "package", "/packages/X", name="X", requires="Y")

        Y = self._create_item(
                "package", "/packages/Y", name="Y")

        self._create_inherited(
                A.get_vpath(), "/node/packages/A")

        self._create_inherited(
                B.get_vpath(), "/node/packages/B")

        self._create_inherited(
                C.get_vpath(), "/node/packages/C")

        self._create_inherited(
                X.get_vpath(), "/node/packages/X")

        self._create_inherited(
                Y.get_vpath(), "/node/packages/Y")

        errors = self.plugin.validate_model(self.api)

        self.assertEquals(0, len(errors))
