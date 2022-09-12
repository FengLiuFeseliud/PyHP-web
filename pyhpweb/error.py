

class IncludeImportError(Exception):
    """包含页面引入失败"""

    def __init__(self, msg, *args: object) -> None:
        super().__init__(*args)
        self.msg = msg
    
    def __str__(self) -> str:
        return self.msg