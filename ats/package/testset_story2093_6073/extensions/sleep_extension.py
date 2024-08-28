from litp.core.extension import ModelExtension
from litp.core.model_type import ItemType
from litp.core.model_type import Property
from time import sleep

class SleepExtension(ModelExtension):
    def define_item_types(self):
        sleep(0.2)
        return [
            ItemType(
                "test_item"
            ),
        ]
