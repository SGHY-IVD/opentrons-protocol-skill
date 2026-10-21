# 模块并发配套API

来源：Opentrons开源protocol_context.py，提交`05b494ba81636978fb79f08bbc20468f94464d5c`；核对日期2026-10-16。签名/类型/默认值与说明按源码提取；公开成员集合与官方参考页核对。仅API 2.30范围，不把edge新增2.31接口带入。Optional[X]表示X或None；未带默认值参数必填。源码中的文档链接为上游引用，离线使用先查本技能。

## ProtocolContext.wait_for_tasks

类型：方法；最低版本：requires_version(2, 27)。

```python
wait_for_tasks(tasks: list[Task]) -> None
```

Wait for a list of [`Tasks`][opentrons.protocol_api.Task] to complete before executing subsequent commands.

Args:
    tasks (list[Task]): A list of `Task` objects to wait for.

`Task` objects can be commands that are allowed to run concurrently.

源码：protocol_context.py L1325–L1334（固定提交）。

## ProtocolContext.create_timer

类型：方法；最低版本：requires_version(2, 27)。

```python
create_timer(seconds: float) -> Task
```

Create a timer [`Task`][opentrons.protocol_api.Task] that runs in the background.

Args:
    seconds (float): The time to delay in seconds.

This timer will continue to run until it is complete and will not block
    subsequent commands. There is no notification when the timer is complete.

源码：protocol_context.py L1338–L1348（固定提交）。

Task对象由并发命令返回，等待其完成不等于停用模块。不要在start/set_target返回后立即假定达到目标；依赖目标温度/转速或循环完成的操作前等待相应任务。协议结束前处理尚未完成任务，停用命令不是取消任意后台任务的通用替代。
## Task.created_at

类型：只读属性；最低版本：requires_version(2, 27)。

```python
created_at: datetime
```

The timestamp of when the task was created.

源码：tasks.py L26–L28（固定提交）。

## Task.done

类型：只读属性；最低版本：requires_version(2, 27)。

```python
done: bool
```

Returns `True` if the task is done.

源码：tasks.py L32–L34（固定提交）。

## Task.started

类型：只读属性；最低版本：requires_version(2, 27)。

```python
started: bool
```

Returns `True` if the task has started.

源码：tasks.py L38–L41（固定提交）。

## Task.finished_at

类型：只读属性；最低版本：requires_version(2, 27)。

```python
finished_at: datetime | None
```

The timestamp of the when the task finished.

Returns `None` if the task hasn't finished yet.

源码：tasks.py L45–L50（固定提交）。

