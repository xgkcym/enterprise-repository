from importlib import import_module

__all__ = ["run_agent", "summarize_trace", "build_run_report", "print_run_report"]


def __getattr__(name: str):
    if name in __all__:
        runner = import_module("src.agent.runner")
        return getattr(runner, name)
    raise AttributeError(f"module 'src.agent' has no attribute {name!r}")
