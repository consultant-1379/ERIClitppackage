from litp.core.extension import ModelExtension
from litp.core.model_type import ItemType
from litp.core.model_type import Property


class Dummy313395Extension(ModelExtension):

    def define_item_types(self):
        return [
            ItemType(
                "torf-313395",
                extend_item="software-item",
                prop=Property("basic_string"),
            ),
        ]

