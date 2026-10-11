from esne.esctl.cli import main
from esne.esctl.commands import info


def test_cpu_and_memory(tmp_path):
    cpu = tmp_path / "cpuinfo"
    cpu.write_text("processor\t: 0\nmodel name\t: AMD Custom APU 0405\n")
    mem = tmp_path / "meminfo"
    mem.write_text("MemTotal:       16384000 kB\nMemFree: 1 kB\n")
    assert info.read_cpu_model(cpu) == "AMD Custom APU 0405"
    assert info.read_memory_mb(mem) == 16000
    assert info.read_cpu_model(tmp_path / "absent") == ""
    assert info.read_memory_mb(tmp_path / "absent") is None


def test_output_format(capsys):
    assert main(["info", "--full"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines
    for line in lines:
        label, sep, value = line.partition(":")
        assert sep and label == label.upper() and value and ":" not in value


def test_values_never_contain_colon():
    assert info._clean("a:b  c") == "a b c"


def test_bad_option_and_has(capsys):
    assert main(["info", "--nope"]) == 2
    assert main(["has", "info"]) == 0
