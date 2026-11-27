# Python 3.13+ 核心语法、内置函数与反射教程

> 兼容基线：Python 3.13  
> 版本补充：Python 3.14  
> 更新时间：2026-09-22

## 1. 文档范围

本文件把三个容易混淆的范围分开：

1. Python 语言语法：关键字、表达式、简单语句、复合语句、函数、类、异常、上下文管理、异步语法和模式匹配。
2. Python 内置对象：官方内置索引中的函数、构造器和装饰器，共 71 个条目。
3. 反射与动态属性：getattr()、setattr()、delattr()、hasattr()、dir()、vars()、描述符和属性查找。

本文件不等同于整个 Python 标准库参考。str.replace()、dict.get()、pathlib.Path、asyncio 等属于内置类型方法或标准库 API，应另行维护。

官方参考：

- [Python 3.13 内置函数](https://docs.python.org/3.13/library/functions.html)
- [Python 3.14 内置函数](https://docs.python.org/3.14/library/functions.html)
- [Python 3.13 语言参考](https://docs.python.org/3.13/reference/index.html)
- [Python 3.14 语言参考](https://docs.python.org/3.14/reference/index.html)
- [Python 3.13 完整 PEG 文法](https://docs.python.org/3.13/reference/grammar.html)
- [Python 3.14 完整 PEG 文法](https://docs.python.org/3.14/reference/grammar.html)

Python 3.13+ 不是一个固定版本号。本文以 3.13 作为最低兼容基线，并把 3.14 新增能力单独标注。使用 3.15 或更高版本时，应再次核对对应版本的 What’s New 文档。

## 2. 函数签名记法

~~~python
def example(positional_only, /, positional_or_keyword, *args,
            keyword_only, **kwargs):
    ...
~~~

| 记号 | 含义 |
|---|---|
| / | 左侧参数只能按位置传递 |
| * | 右侧参数只能按关键字传递 |
| *args | 收集多余的位置参数，结果为元组 |
| **kwargs | 收集多余的关键字参数，结果为字典 |
| name=value | 带默认值的参数 |
| -> T | 返回值注解，不自动执行运行时类型检查 |

例如：

~~~python
def query(
    table: str,
    /,
    limit: int = 20,
    *,
    descending: bool = False,
) -> list[str]:
    return []


query("users")
query("users", 50, descending=True)
~~~

table 只能按位置传入，descending 只能按关键字传入。

## 3. getattr、setattr 与属性反射

### 3.1 函数对照表

| 函数 | 作用 | 常见等价形式 |
|---|---|---|
| getattr(obj, name) | 动态读取属性 | obj.name |
| setattr(obj, name, value) | 动态设置属性 | obj.name = value |
| delattr(obj, name) | 动态删除属性 | del obj.name |
| hasattr(obj, name) | 判断读取是否产生 AttributeError | 无完全等价语法 |
| dir(obj) | 获取交互式探索用的名称列表 | 无完全等价语法 |
| vars(obj) | 获取对象的 __dict__ | obj.__dict__ |
| type(obj) | 获取精确运行时类型 | obj.__class__ |
| isinstance(obj, T) | 判断实例及子类关系 | 推荐的类型判断方式 |
| issubclass(C, T) | 判断类继承关系 | 类级别类型判断 |
| callable(obj) | 判断对象是否看起来可调用 | 检查 __call__ 能力 |

### 3.2 getattr()

签名：

~~~python
getattr(object, name, /)
getattr(object, name, default, /)
~~~

- object 是目标对象。
- name 必须是字符串。
- 没有 default 且属性不存在时抛出 AttributeError。
- 有 default 时，属性查找产生 AttributeError 才返回默认值。
- 读取过程会经过 __getattribute__()、描述符和可能的 __getattr__()。

~~~python
class User:
    def __init__(self, name: str) -> None:
        self.name = name


user = User("Alice")

print(getattr(user, "name"))
print(getattr(user, "age", 0))
~~~

使用唯一哨兵区分“属性不存在”和“属性值就是 None”：

~~~python
MISSING = object()

value = getattr(user, "nickname", MISSING)

if value is MISSING:
    print("属性不存在")
else:
    print(f"属性存在：{value!r}")
~~~

名称只要求是字符串，不要求是合法 Python 标识符：

~~~python
setattr(user, "display-name", "Alice")
print(getattr(user, "display-name"))
~~~

点号语法不能读取 display-name，因为它会被解析为减法表达式。

### 3.3 setattr()

签名：

~~~python
setattr(object, name, value, /)
~~~

它通常等价于 object.name = value，返回值始终为 None。设置时可能触发：

- 自定义的 __setattr__()；
- property 或其他数据描述符的 __set__()；
- __slots__ 的限制；
- 只读属性的 AttributeError。

~~~python
class User:
    pass


user = User()

setattr(user, "name", "Alice")
setattr(user, "age", 20)

print(user.name)
print(user.age)
~~~

来自外部的动态字段必须使用白名单：

~~~python
ALLOWED_FIELDS = {"name", "age"}

for field_name, field_value in payload.items():
    if field_name not in ALLOWED_FIELDS:
        raise ValueError(f"不允许设置字段：{field_name}")

    setattr(user, field_name, field_value)
~~~

### 3.4 delattr()

签名：

~~~python
delattr(object, name, /)
~~~

通常等价于 del object.name，可能调用 __delattr__() 或描述符的 __delete__()：

~~~python
class User:
    def __init__(self) -> None:
        self.nickname = "Alice"


user = User()
delattr(user, "nickname")
~~~

属性不存在时通常会抛出 AttributeError。

### 3.5 hasattr()

hasattr() 的行为近似于：

~~~python
def approximate_hasattr(obj: object, name: str) -> bool:
    try:
        getattr(obj, name)
    except AttributeError:
        return False
    else:
        return True
~~~

因此，属性 getter 内部故意或意外抛出 AttributeError 时，异常可能被误判为“属性不存在”：

~~~python
class BrokenConfig:
    @property
    def token(self) -> str:
        raise AttributeError("读取配置失败")


print(hasattr(BrokenConfig(), "token"))
# False
~~~

需要诊断错误时，应直接访问并捕获异常：

~~~python
try:
    token = config.token
except AttributeError as exc:
    print(f"属性读取失败：{exc}")
~~~

hasattr() 只吞掉 AttributeError，不会吞掉 RuntimeError、ValueError 等其他异常。

### 3.6 默认属性查找顺序

在默认的 object.__getattribute__() 机制下，实例读取 obj.name 大致遵循：

~~~text
obj.name
  |
  +-- 1. 类及 MRO 中的数据描述符
  |      例如带 setter 的 property
  |
  +-- 2. 实例的 __dict__
  |
  +-- 3. 类及 MRO 中的普通属性或非数据描述符
  |      例如普通方法
  |
  +-- 4. 查找失败后调用 __getattr__()
~~~

自定义 __getattribute__() 可以改变整个过程。实现它时必须避免递归：

~~~python
class LoggedObject:
    def __getattribute__(self, name: str) -> object:
        print(f"读取属性：{name}")
        return object.__getattribute__(self, name)
~~~

不要在 __getattribute__() 中直接写 self.__dict__，因为读取 __dict__ 本身也会再次调用 __getattribute__()。

官方参考：[属性访问](https://docs.python.org/3.14/reference/expressions.html#attribute-references) 和 [描述符调用](https://docs.python.org/3.14/reference/datamodel.html#invoking-descriptors)。

### 3.7 property 与 setattr()

~~~python
class User:
    def __init__(self, age: int) -> None:
        self._age = age

    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int) -> None:
        if value < 0:
            raise ValueError("年龄不能小于 0")

        self._age = value


user = User(20)
setattr(user, "age", 21)
print(user.age)
~~~

setattr() 不会绕过 property 的 setter。只读属性设置时会抛出 AttributeError。

### 3.8 __slots__ 与动态属性

~~~python
class User:
    __slots__ = ("name", "age")

    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age


user = User("Alice", 20)
setattr(user, "name", "Bob")

setattr(user, "email", "alice@example.com")
# AttributeError：email 不在 __slots__ 中
~~~

没有 __dict__ 槽位的实例通常不能使用 vars(user)。

### 3.9 双下划线名称改写

名称改写发生在编译阶段：

~~~python
class Account:
    def __init__(self) -> None:
        self.__token = "secret"


account = Account()
print(account.__dict__)
# {'_Account__token': 'secret'}
~~~

动态访问时必须使用改写后的名称：

~~~python
getattr(account, "_Account__token")
setattr(account, "_Account__token", "new-secret")
delattr(account, "_Account__token")
~~~

这不是安全机制，只是避免子类名称冲突的约定。

### 3.10 dir() 与 vars()

dir() 主要面向交互式探索，不保证是完整、稳定的 API 清单。对象实现 __dir__() 时，dir() 会调用它。

~~~python
class API:
    def __dir__(self) -> list[str]:
        return ["start", "stop", "status"]


print(dir(API()))
~~~

vars(obj) 有参数时通常等价于 obj.__dict__：

~~~python
class User:
    def __init__(self) -> None:
        self.name = "Alice"
        self.age = 20


print(vars(User()))
~~~

无参数 vars() 的行为与 locals() 相同。

### 3.11 静态属性检查

普通 getattr() 可能执行 property、描述符或动态属性逻辑。需要查看原始类结构时，可使用 inspect.getattr_static() 或 Python 3.11+ 的 inspect.getmembers_static()：

~~~python
import inspect


raw_value = inspect.getattr_static(user, "age")
members = inspect.getmembers_static(user)
~~~

静态检查可能得到描述符本身，也可能看不到动态生成的属性。

参考：[inspect.getmembers_static()](https://docs.python.org/3.14/library/inspect.html#inspect.getmembers_static)。

### 3.12 动态方法调用

~~~python
class Service:
    def start(self) -> str:
        return "started"

    def stop(self) -> str:
        return "stopped"


service = Service()
command = "start"

allowed = {"start", "stop"}
if command not in allowed:
    raise ValueError(f"不支持的命令：{command}")

method = getattr(service, command)
if not callable(method):
    raise TypeError("目标属性不可调用")

print(method())
~~~

当命令集合固定时，显式映射往往更安全：

~~~python
handlers = {
    "start": service.start,
    "stop": service.stop,
}

print(handlers[command]())
~~~

官方属性参考：[数据模型中的属性和描述符](https://docs.python.org/3.14/reference/datamodel.html#customizing-attribute-access)。

## 4. 全部 71 个内置函数、构造器与装饰器

官方页面把普通函数、内置类型构造器和装饰器放在同一个索引中。以下清单按用途分组。

### 4.1 属性、类型与对象模型

| 名称 | 签名 | 作用与关键注意点 |
|---|---|---|
| callable | callable(obj, /) | 判断对象是否看起来可调用；True 仍不保证实际调用成功 |
| classmethod | classmethod(function) | 转换为类方法，第一个隐式参数是 cls |
| delattr | delattr(obj, name, /) | 动态删除属性，可能触发 __delattr__ 或描述符 |
| dir | dir()、dir(obj, /) | 返回用于探索的名称列表，不保证完整 |
| getattr | getattr(obj, name[, default], /) | 动态读取属性 |
| globals | globals() | 当前模块全局命名空间的实际字典 |
| hasattr | hasattr(obj, name, /) | 读取属性并捕获 AttributeError |
| hash | hash(obj, /) | 返回哈希值；相等对象必须具有相等哈希 |
| id | id(obj, /) | 对象生命周期内唯一标识，不能当持久化 ID |
| isinstance | isinstance(obj, classinfo, /) | 判断实例及子类关系 |
| issubclass | issubclass(cls, classinfo, /) | 判断类的继承关系 |
| locals | locals() | 返回当前局部命名空间；函数内不要依赖修改结果写回局部变量 |
| object | object() | 所有新式类的最终基类 |
| property | property(fget=None, fset=None, fdel=None, doc=None) | 创建数据描述符属性 |
| setattr | setattr(obj, name, value, /) | 动态设置属性 |
| staticmethod | staticmethod(function) | 创建不绑定实例和类的静态方法 |
| super | super()、super(type, obj_or_type, /) | 按 MRO 查找后续实现 |
| type | type(obj, /)、type(name, bases, namespace, /, **kwargs) | 获取精确类型或动态创建类 |
| vars | vars()、vars(obj, /) | 无参数类似 locals()；有参数返回 __dict__ |

### 4.2 动态执行、导入、帮助与调试

| 名称 | 签名 | 作用与关键注意点 |
|---|---|---|
| breakpoint | breakpoint(*args, **kwargs) | 进入调试器，默认调用 sys.breakpointhook() |
| compile | compile(source, filename, mode, flags=0, dont_inherit=False, optimize=-1) | 编译源码、代码对象或 AST |
| eval | eval(source, /, globals=None, locals=None) | 执行单个表达式并返回结果 |
| exec | exec(source, /, globals=None, locals=None, *, closure=None) | 执行语句，返回 None |
| help | help(request) | 进入交互式帮助系统 |
| __import__ | __import__(name, globals=None, locals=None, fromlist=(), level=0) | import 语句的底层接口，日常更推荐 importlib.import_module() |

### 4.3 迭代、异步迭代与聚合

| 名称 | 签名 | 作用与关键注意点 |
|---|---|---|
| aiter | aiter(async_iterable, /) | 获取异步迭代器；没有 iter() 的双参数形式 |
| anext | anext(async_iterator[, default], /) | 获取异步迭代器的下一个元素，返回可等待对象 |
| all | all(iterable, /) | 所有元素为真时返回 True；空迭代对象返回 True |
| any | any(iterable, /) | 任意元素为真时返回 True；空迭代对象返回 False |
| enumerate | enumerate(iterable, start=0) | 产生序号和元素二元组 |
| filter | filter(function, iterable, /) | 惰性过滤；function=None 时保留真值元素 |
| iter | iter(obj, /) 或 iter(callable, sentinel, /) | 创建迭代器或按哨兵重复调用函数 |
| len | len(obj, /) | 调用长度协议 |
| map | 3.13：map(function, iterable, *iterables)；3.14：增加 strict=False | 惰性映射 |
| max | max(iterable, /, *, default=..., key=None) | 返回最大元素 |
| min | min(iterable, /, *, default=..., key=None) | 返回最小元素 |
| next | next(iterator[, default], /) | 获取下一个元素 |
| range | range(stop) 或 range(start, stop[, step]) | 惰性整数序列 |
| reversed | reversed(sequence, /) | 返回反向迭代器 |
| sorted | sorted(iterable, /, *, key=None, reverse=False) | 返回新的稳定排序列表 |
| sum | sum(iterable, /, start=0) | 数值求和；字符串连接使用 join() |
| zip | zip(*iterables, strict=False) | 并行组合；strict=True 可检查长度 |

### 4.4 数值、字符、字符串和对象表示

| 名称 | 签名 | 作用与关键注意点 |
|---|---|---|
| abs | abs(number, /) | 绝对值；复数返回模 |
| ascii | ascii(obj, /) | 类似 repr()，非 ASCII 字符转义 |
| bin | bin(integer, /) | 转换为带 0b 的二进制字符串 |
| bool | bool(obj=False, /) | 按真值规则转换为布尔值 |
| chr | chr(codepoint, /) | Unicode 码点转字符 |
| complex | complex(number=0, /) 或 complex(real=0, imag=0) | 创建复数 |
| divmod | divmod(a, b, /) | 返回商和余数 |
| float | float(number=0.0, /) 或 float(string, /) | 转换为浮点数 |
| format | format(value, format_spec="", /) | 调用格式化协议 |
| hex | hex(integer, /) | 转换为带 0x 的十六进制字符串 |
| int | int(number=0, /) 或 int(string, /, base=10) | 转换为整数 |
| oct | oct(integer, /) | 转换为带 0o 的八进制字符串 |
| ord | ord(character, /) | 单字符转 Unicode 码点 |
| pow | pow(base, exp, mod=None) | 幂运算；三参数形式用于模幂 |
| repr | repr(obj, /) | 面向开发和调试的对象表示 |
| round | round(number, ndigits=None) | 舍入；浮点数使用偶数优先规则 |
| str | str(obj="") 或 str(bytes, encoding, errors) | 构造文本或解码字节 |

### 4.5 容器、二进制数据与切片

| 名称 | 签名 | 作用与关键注意点 |
|---|---|---|
| bytearray | bytearray(source=b"") | 可变字节序列 |
| bytes | bytes(source=b"") | 不可变字节序列 |
| dict | dict(...) | 映射类型，保持插入顺序 |
| frozenset | frozenset(iterable=(), /) | 不可变集合，可作为字典键 |
| list | list(iterable=(), /) | 可变有序序列 |
| memoryview | memoryview(obj) | 零复制访问缓冲区协议对象 |
| set | set(iterable=(), /) | 可变集合 |
| slice | slice(stop) 或 slice(start, stop, step=None) | 表示切片规则 |
| tuple | tuple(iterable=(), /) | 不可变有序序列 |

### 4.6 输入、输出与文件

| 名称 | 签名 | 作用与关键注意点 |
|---|---|---|
| input | input(prompt="", /) | 读取一行并返回字符串 |
| open | open(file, mode="r", buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None) | 打开文件；文本文件建议明确 encoding |
| print | print(*objects, sep=" ", end="\\n", file=None, flush=False) | 输出对象 |

### 4.7 常用内置函数示例

#### bool 与真值测试

以下对象通常为假：

~~~python
False
None
0
0.0
0j
""
b""
[]
()
{}
set()
range(0)
~~~

~~~python
bool("False")
# True，因为非空字符串为真
~~~

#### 数值转换

~~~python
int("101", 2)
int("ff", 16)
float("3.14")
complex("1+2j")
~~~

浮点数转整数是向零截断：

~~~python
int(3.9)
# 3

int(-3.9)
# -3
~~~

#### 字符和码点

~~~python
ord("A")
# 65

chr(65)
# "A"
~~~

#### repr、str 与 ascii

~~~python
text = "你好"

str(text)
# 你好

repr(text)
# '你好'

ascii(text)
# '\\u4f60\\u597d'
~~~

#### all、any、enumerate

~~~python
values = [2, 4, 6]

all(value % 2 == 0 for value in values)
# True

any(value > 5 for value in values)
# True

for index, value in enumerate(values, start=1):
    print(index, value)
~~~

#### iter 的哨兵形式

~~~python
from functools import partial


with open("data.bin", "rb") as file:
    read_block = partial(file.read, 4096)

    for block in iter(read_block, b""):
        print(len(block))
~~~

#### sorted、max 与 min

~~~python
records = [
    {"name": "Alice", "score": 90},
    {"name": "Bob", "score": 80},
    {"name": "Carol", "score": 90},
]

result = sorted(
    records,
    key=lambda item: item["score"],
    reverse=True,
)

best = max(records, key=lambda item: item["score"])
~~~

空迭代对象可使用 default：

~~~python
max([], default=None)
min([], default=None)
~~~

#### zip 的严格长度检查

~~~python
names = ["Alice", "Bob"]
ages = [20, 30]

pairs = list(zip(names, ages, strict=True))
~~~

长度不相等时会抛出 ValueError：

~~~python
list(zip(["Alice"], [20, 30], strict=True))
~~~

#### range

~~~python
list(range(5))
# [0, 1, 2, 3, 4]

list(range(2, 10, 2))
# [2, 4, 6, 8]
~~~

range 不会预先创建整个整数列表，适合表示大范围。

#### bytes、bytearray 和 memoryview

~~~python
immutable_data = bytes([65, 66, 67])
mutable_data = bytearray(b"ABC")

mutable_data[0] = 90
print(mutable_data)
# bytearray(b'ZBC')
~~~

~~~python
data = bytearray(b"abcdef")
view = memoryview(data)
view[1:4] = b"XYZ"
print(data)
# bytearray(b'aXYZef')
~~~

#### open

~~~python
from pathlib import Path


path = Path("config.txt")

with path.open("r", encoding="utf-8") as file:
    content = file.read()
~~~

常用模式：

| 模式 | 作用 |
|---|---|
| r | 文本读取 |
| w | 覆盖写入 |
| a | 追加写入 |
| x | 文件不存在时创建 |
| b | 二进制模式 |
| + | 同时读写 |

#### breakpoint

~~~python
def calculate(value: int) -> int:
    breakpoint()
    return value * 2
~~~

不想进入调试器时，可以在运行环境中设置环境变量 PYTHONBREAKPOINT=0。

## 5. Python 语言语法

### 5.1 缩进、物理行与逻辑行

Python 使用缩进表示代码块：

~~~python
if condition:
    do_something()
    do_another_thing()
~~~

推荐使用括号自动续行：

~~~python
result = calculate(
    first_argument,
    second_argument,
    third_argument,
)
~~~

不要混用制表符和空格。工程中通常统一使用 4 个空格。

### 5.2 关键字与软关键字

保留关键字：

~~~text
False None True and as assert async await break class continue def del
elif else except finally for from global if import in is lambda nonlocal
not or pass raise return try while with yield
~~~

软关键字：

~~~text
match case _ type
~~~

match、case 和下划线在模式匹配语境中有特殊含义，type 在类型别名语句中有特殊含义。

### 5.3 标识符

~~~python
name
user_name
_private
value2
~~~

标识符不能以数字开头，区分大小写，不能使用保留关键字。

### 5.4 字面量

~~~python
none_value = None
enabled = True
integer = 1_000
binary = 0b1010
octal = 0o755
hexadecimal = 0xFF
floating = 3.14
complex_number = 2 + 3j
text = "hello"
bytes_value = b"hello"
ellipsis_value = ...
~~~

字符串前缀常见形式：

~~~python
r"C:\\users\\name"
b"ABC"
f"{value}"
~~~

Python 3.14 新增模板字符串：

~~~python
template = t"Hello {name}"
~~~

参考：[t-string](https://docs.python.org/3.14/reference/lexical_analysis.html#t-strings)。

### 5.5 容器显示和解包

~~~python
items = [1, 2, 3]
point = (10, 20)
mapping = {"name": "Alice"}
roles = {"admin", "user"}
~~~

~~~python
left = [1, 2]
right = [3, 4]
combined = [*left, *right]
~~~

~~~python
base = {"name": "Alice", "age": 20}
override = {"age": 30}
result = {**base, **override}
~~~

后面展开的字典键覆盖前面的同名键。

### 5.6 推导式

~~~python
squares = [
    number * number
    for number in range(10)
    if number % 2 == 0
]
~~~

~~~python
mapping = {
    name: len(name)
    for name in names
}
~~~

~~~python
generator = (
    number * number
    for number in range(10)
)
~~~

生成器表达式按需计算，不能当作已经生成的列表。

### 5.7 运算符

算术运算：

~~~text
+  -  *  /  //  %  **  @
~~~

比较运算：

~~~text
<  <=  >  >=  ==  !=  is  is not  in  not in
~~~

布尔运算：

~~~text
not  and  or
~~~

位运算：

~~~text
&  |  ^  ~  <<  >>
~~~

and 和 or 返回操作数而不是强制返回布尔值：

~~~python
value = configured_value or default_value
~~~

### 5.8 比较链

~~~python
0 <= value < 100
~~~

近似等价于：

~~~python
0 <= value and value < 100
~~~

中间表达式只计算一次。

### 5.9 条件表达式

~~~python
label = "adult" if age >= 18 else "minor"
~~~

### 5.10 赋值表达式

~~~python
if (match := pattern.search(text)) is not None:
    print(match.group())
~~~

赋值表达式 := 需要注意括号和可读性，不应代替所有普通赋值。

### 5.11 lambda

~~~python
users.sort(key=lambda user: user.age)
~~~

lambda 只能包含一个表达式，复杂流程应使用普通 def。

### 5.12 运算符优先级

从高到低大致为：

~~~text
括号、显示、推导式
属性、下标、切片、调用
await
**
+x、-x、~x
*、@、/、//、%
+、-
<<、>>
&
^
|
比较、in、not in、is、is not
not
and
or
条件表达式
lambda
:=
~~~

例如：

~~~python
-2 ** 2
# -4

(-2) ** 2
# 4
~~~

## 6. 简单语句

### 6.1 赋值

~~~python
name = "Alice"
left = right = []
~~~

赋值是名称绑定，不是自动复制：

~~~python
left = [1, 2]
right = left
right.append(3)
print(left)
# [1, 2, 3]
~~~

### 6.2 增强赋值

~~~python
count += 1
total *= 2
items += other_items
~~~

增强赋值可能原地修改，也可能创建新对象，取决于类型实现。

### 6.3 注解赋值

~~~python
name: str = "Alice"
count: int
~~~

注解默认不会自动进行运行时类型检查。

### 6.4 assert

~~~python
assert condition, "错误信息"
~~~

不要使用 assert 作为必须执行的业务校验，因为优化模式可以移除断言。业务校验应显式抛出 ValueError 等异常。

### 6.5 pass

~~~python
class Placeholder:
    pass
~~~

### 6.6 del

~~~python
del variable
del obj.attribute
del items[index]
del mapping[key]
~~~

删除名称绑定不等于保证对象立即销毁。

### 6.7 return

~~~python
def add(left: int, right: int) -> int:
    return left + right
~~~

没有表达式的 return 等价于 return None。

### 6.8 yield 和 yield from

~~~python
def numbers():
    yield 1
    yield 2


def combined():
    yield from range(3)
    yield from range(10, 13)
~~~

生成器函数调用时返回生成器对象，不会立即执行完整函数。

### 6.9 raise

~~~python
raise ValueError("无效参数")
~~~

保留异常链：

~~~python
try:
    value = int(text)
except ValueError as exc:
    raise ConfigurationError("配置格式错误") from exc
~~~

隐藏直接上下文：

~~~python
raise ConfigurationError("配置格式错误") from None
~~~

### 6.10 break 和 continue

~~~python
for item in items:
    if should_skip(item):
        continue
    if should_stop(item):
        break
    process(item)
~~~

### 6.11 import

~~~python
import pathlib
from pathlib import Path
import numpy as np
~~~

推荐显式导入名称，谨慎使用 from module import *。

### 6.12 global 和 nonlocal

~~~python
counter = 0


def increment() -> None:
    global counter
    counter += 1
~~~

~~~python
def create_counter():
    count = 0

    def increment() -> int:
        nonlocal count
        count += 1
        return count

    return increment
~~~

### 6.13 type 类型别名

Python 3.12+：

~~~python
type UserId = int
type Coordinates = tuple[float, float]
type Result[T] = T | Exception
~~~

## 7. 复合语句

### 7.1 if

~~~python
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
else:
    grade = "C"
~~~

### 7.2 while 与 else

~~~python
attempt = 0

while attempt < 3:
    if operation_succeeded():
        break
    attempt += 1
else:
    raise RuntimeError("所有尝试均失败")
~~~

循环自然结束时执行 else；使用 break 时不执行。

### 7.3 for 与 else

~~~python
for user in users:
    if user.identifier == target_id:
        found = user
        break
else:
    raise LookupError("用户不存在")
~~~

### 7.4 try、except、else、finally

~~~python
try:
    value = load_value()
except FileNotFoundError:
    value = default_value()
except ValueError as exc:
    raise ConfigurationError("格式错误") from exc
else:
    use_value(value)
finally:
    release_resources()
~~~

异常处理应从具体类型到宽泛类型排列。

### 7.5 except*

Python 3.11+：

~~~python
try:
    raise ExceptionGroup(
        "多个错误",
        [ValueError("值错误"), TypeError("类型错误")],
    )
except* ValueError as group:
    print(group)
except* TypeError as group:
    print(group)
~~~

普通 except 和 except* 不能混用在同一个 try 分支集合中。

### 7.6 with

~~~python
with open("data.txt", encoding="utf-8") as file:
    content = file.read()
~~~

同步上下文管理器实现：

~~~text
__enter__()
__exit__(exc_type, exc_value, traceback)
~~~

__exit__() 返回真值时会抑制异常。

多个上下文：

~~~python
with (
    open("source.txt", encoding="utf-8") as source,
    open("target.txt", "w", encoding="utf-8") as target,
):
    target.write(source.read())
~~~

退出顺序与进入顺序相反。

### 7.7 match 和 case

~~~python
def handle(message: object) -> str:
    match message:
        case {"type": "text", "content": str(content)}:
            return content
        case {"type": "image", "url": str(url)}:
            return url
        case _:
            return "unknown"
~~~

支持字面量、捕获、通配符、OR、AS、序列、映射、类模式和 guard：

~~~python
match value:
    case 0 | 1:
        print("小值")
    case int(number) if number > 10:
        print(number)
    case _:
        print("其他")
~~~

裸名称通常是捕获模式，不是全局常量比较。常量匹配应使用字面量或限定名称。

### 7.8 def 和 class

~~~python
class User:
    def __init__(self, name: str) -> None:
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}"
~~~

### 7.9 async def、async for、async with

~~~python
async def fetch_data() -> str:
    return "data"


async def main() -> None:
    result = await fetch_data()
    print(result)
~~~

~~~python
async for message in message_stream:
    process(message)
~~~

~~~python
async with client.session() as session:
    await session.send(data)
~~~

目标对象需要实现对应的异步协议：__await__、__aiter__、__anext__、__aenter__ 和 __aexit__。

## 8. 类、描述符和特殊方法

### 8.1 实例方法、类方法和静态方法

~~~python
class User:
    total = 0

    def __init__(self, name: str) -> None:
        self.name = name
        type(self).total += 1

    def greet(self) -> str:
        return f"Hello, {self.name}"

    @classmethod
    def anonymous(cls) -> "User":
        return cls("anonymous")

    @staticmethod
    def normalize_name(name: str) -> str:
        return name.strip().title()
~~~

| 类型 | 隐式参数 | 典型用途 |
|---|---|---|
| 实例方法 | self | 访问实例状态 |
| 类方法 | cls | 替代构造器或访问类状态 |
| 静态方法 | 无 | 与类相关但不依赖实例的工具函数 |

### 8.2 常见特殊方法

| 方法 | 触发位置 |
|---|---|
| __init__ | 初始化实例 |
| __new__ | 创建实例 |
| __repr__ | repr(obj) |
| __str__ | str(obj) 和 print(obj) |
| __len__ | len(obj) |
| __bool__ | bool(obj) |
| __iter__ | iter(obj)、for |
| __next__ | next(iterator) |
| __getitem__ | obj[key] |
| __setitem__ | obj[key] = value |
| __delitem__ | del obj[key] |
| __contains__ | item in obj |
| __call__ | obj() |
| __enter__、__exit__ | with |
| __aenter__、__aexit__ | async with |
| __getattribute__ | 属性读取 |
| __getattr__ | 属性查找失败回退 |
| __setattr__ | 属性设置 |
| __delattr__ | 属性删除 |
| __hash__ | hash(obj) |
| __eq__ | obj1 == obj2 |

隐式特殊方法查找通常发生在类型上，而不是实例字典上：

~~~python
class Sized:
    def __len__(self) -> int:
        return 10


value = Sized()
value.__len__ = lambda: 99

print(value.__len__())
# 99

print(len(value))
# 10
~~~

参考：[特殊方法查找](https://docs.python.org/3.14/reference/datamodel.html#special-method-lookup)。

## 9. 函数定义、调用和装饰器

### 9.1 完整参数形式

~~~python
def request(
    url: str,
    /,
    method: str = "GET",
    *path_parts: str,
    timeout: float = 10.0,
    **headers: str,
) -> dict[str, object]:
    return {
        "url": url,
        "method": method,
        "parts": path_parts,
        "timeout": timeout,
        "headers": headers,
    }
~~~

调用：

~~~python
request(
    "/users",
    "POST",
    "active",
    timeout=5.0,
    authorization="token",
)
~~~

### 9.2 调用时解包

~~~python
def add(left: int, right: int) -> int:
    return left + right


arguments = (10, 20)
print(add(*arguments))
~~~

~~~python
arguments = {
    "left": 10,
    "right": 20,
}

print(add(**arguments))
~~~

同一个参数不能被重复传递。

### 9.3 装饰器

~~~python
@decorator
def function():
    ...
~~~

等价于：

~~~python
def function():
    ...


function = decorator(function)
~~~

多个装饰器从下到上应用：

~~~python
@outer
@inner
def function():
    ...
~~~

等价于 outer(inner(function))。

保留函数元数据：

~~~python
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar


R = TypeVar("R")


def trace(function: Callable[..., R]) -> Callable[..., R]:
    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        print(f"调用：{function.__qualname__}")
        return function(*args, **kwargs)

    return wrapper
~~~

### 9.4 闭包和晚绑定

~~~python
def create_multiplier(factor: int):
    def multiply(value: int) -> int:
        return value * factor

    return multiply
~~~

循环变量晚绑定：

~~~python
functions = [
    lambda: index
    for index in range(3)
]

print([function() for function in functions])
# [2, 2, 2]
~~~

使用默认参数保存当前值：

~~~python
functions = [
    lambda index=index: index
    for index in range(3)
]

print([function() for function in functions])
# [0, 1, 2]
~~~

## 10. 异常、上下文和作用域陷阱

### 10.1 finally 中不要随意 return

~~~python
def dangerous() -> int:
    try:
        raise RuntimeError("原始异常")
    finally:
        return 1
~~~

finally 中的 return 可能覆盖原始异常。Python 3.14 对部分 finally 控制流会发出 SyntaxWarning。

### 10.2 locals 的写回语义

Python 3.13 以后，在函数、生成器、协程等优化作用域中，locals() 返回独立快照语义：

~~~python
def example() -> None:
    value = 10
    namespace = locals()
    namespace["value"] = 99
    print(value)
    # 仍为 10
~~~

动态执行时应显式传入命名空间：

~~~python
def execute() -> dict[str, object]:
    namespace: dict[str, object] = {}
    exec("result = 10 + 20", {}, namespace)
    return namespace
~~~

## 11. 导入语法

### 11.1 基础导入

~~~python
import pathlib
from pathlib import Path
import numpy as np
~~~

### 11.2 相对导入

~~~python
from . import sibling
from .module import name
from ..parent_module import name
~~~

相对导入依赖当前模块的包上下文。

### 11.3 星号导入

~~~python
from module import *
~~~

不推荐，因为名称来源不清晰、可能覆盖已有名称，也不利于静态分析。

### 11.4 动态导入

推荐：

~~~python
from importlib import import_module


module = import_module("package.module")
~~~

日常代码不建议直接调用 __import__()。

## 12. Python 3.13 与 3.14 差异

| 内容 | Python 3.13 | Python 3.14 |
|---|---|---|
| locals() | PEP 667 定义优化作用域快照语义 | 沿用 |
| vars() | 无参行为跟随 locals() | 沿用 |
| eval() / exec() | globals、locals 可按关键字传递 | 沿用 |
| property.__name__ | 新增且可读写 | 沿用 |
| classmethod 包装其他 descriptor | 已移除 | 沿用 |
| map(strict=...) | 不支持 | 新增 |
| int() | 处于不再依赖 __trunc__() 的迁移阶段 | 不再委托 __trunc__() |
| complex(real, imag) | 旧行为 | 传入复数进入弃用 |
| sum() | 浮点求和已有精度改进 | 复数使用专门求和算法 |
| super 对象 | 普通代理 | 支持复制和 pickle |
| memoryview | 普通类型 | 支持泛型下标 |
| bool(NotImplemented) | 已有弃用警告 | 抛出 TypeError |
| t-string | 不支持 | 新增 t"..." 模板字符串 |
| 注解求值 | 旧模型 | 默认延迟求值的新模型 |

官方变更：

- [What’s New in Python 3.13](https://docs.python.org/3.13/whatsnew/3.13.html)
- [What’s New in Python 3.14](https://docs.python.org/3.14/whatsnew/3.14.html)

### 12.1 Python 3.14 的 map(strict=True)

Python 3.13：

~~~python
map(function, iterable, *iterables)
~~~

Python 3.14：

~~~python
map(function, iterable, *iterables, strict=False)
~~~

兼容 3.13 和 3.14 的严格写法：

~~~python
result = [
    function(left_item, right_item)
    for left_item, right_item in zip(
        left,
        right,
        strict=True,
    )
]
~~~

### 12.2 Python 3.13 的 locals、eval 和 exec

函数内部不要依赖修改 locals() 写回局部变量。动态执行需要显式命名空间：

~~~python
namespace: dict[str, object] = {}
exec("result = 10 + 20", {}, namespace)
print(namespace["result"])
~~~

## 13. 安全和工程建议

1. 不要把不可信输入传给 eval()、exec() 或动态 compile()。
2. 外部输入驱动 getattr() 或 setattr() 时使用允许列表。
3. 不要把 hasattr() 当作完整异常诊断工具。
4. 不要把 dir() 当作稳定、完整的公共 API 清单。
5. 不要把 id() 当作数据库主键或持久化标识。
6. 可变对象作为字典键或集合元素会破坏哈希不变量。
7. 文本文件使用 open() 时显式指定编码。
8. 等长数据并行处理时使用 zip(strict=True)。
9. 不要用 assert 作为必须执行的业务校验。
10. 不要依赖修改函数内部 locals() 来改变局部变量。
11. 不要在 finally 中用 return 覆盖异常。
12. 模式匹配中，裸名称通常是捕获模式。

## 14. 常见错误速查

| 错误 | 正确方向 |
|---|---|
| 用 is 比较普通值 | 用 ==；只对 None 等单例使用 is |
| 认为赋值会复制对象 | 根据需要使用浅复制或深复制 |
| 使用可变默认参数 | 使用 None 哨兵 |
| 用 hasattr() 掩盖 getter 异常 | 直接读取并捕获异常 |
| 认为 dir() 返回全部属性 | 使用类定义、vars() 和 inspect 综合判断 |
| 用 type(obj) is T 判断所有子类 | 使用 isinstance(obj, T) |
| 对不可信输入使用 eval() | 使用白名单、解析器或 ast.literal_eval() |
| 用 sum() 拼接字符串 | 使用 "".join(strings) |
| 忘记 zip() 会截断较长迭代器 | 使用 strict=True |
| 误以为生成器已立即执行 | 显式迭代或转换为列表 |
| 在 finally 中 return | 让异常正常传播 |
| 将 case NAME 当作常量匹配 | 使用字面量或限定名称 |
| 认为类型注解自动校验 | 使用类型检查器或显式运行时校验 |

## 15. 相关标准库工具

以下工具不是内置函数，但经常和 getattr()、setattr() 一起使用：

| 工具 | 用途 |
|---|---|
| operator.attrgetter() | 按属性读取，适合 sorted()、map() |
| operator.itemgetter() | 按下标或键读取 |
| operator.methodcaller() | 动态调用方法 |
| inspect.getattr_static() | 不执行 descriptor 的静态属性读取 |
| inspect.getmembers_static() | 静态列出成员 |
| inspect.signature() | 查看函数签名 |
| ast.literal_eval() | 安全解析有限 Python 字面量 |
| importlib.import_module() | 推荐的动态导入接口 |

参考：

- [operator 模块](https://docs.python.org/3.14/library/operator.html)
- [inspect 模块](https://docs.python.org/3.14/library/inspect.html)
- [ast.literal_eval](https://docs.python.org/3.14/library/ast.html#ast.literal_eval)
- [importlib.import_module](https://docs.python.org/3.14/library/importlib.html#importlib.import_module)

## 16. 文档集拆分建议

如果要长期维护，不建议把所有内容塞进一个巨型文件。可以继续拆分为：

~~~text
docs/07_语言参考与架构图/Python3.13+/
├── README.md
├── 00-范围与版本约定.md
├── 01-词法分析与字面量.md
├── 02-表达式与运算符.md
├── 03-简单语句.md
├── 04-复合语句.md
├── 05-函数与调用.md
├── 06-类与对象模型.md
├── 07-属性反射与描述符.md
├── 08-异常与上下文管理.md
├── 09-迭代器与生成器.md
├── 10-异步编程语法.md
├── 11-模式匹配.md
├── 12-类型注解与泛型.md
├── 13-导入与作用域.md
├── 14-内置函数总览.md
├── 15-Python-3.13-3.14版本差异.md
└── 16-完整语法速查.md
~~~

本文件覆盖语言语法与 71 个内置条目；内置类型的全部方法和整个标准库 API 不属于同一篇文档的合理范围。
