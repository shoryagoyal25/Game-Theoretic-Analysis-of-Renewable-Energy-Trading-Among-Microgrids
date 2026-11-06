import pytest
from microgrid import Microgrid

def test_energy_balance():
    g = Microgrid("A", 80, 50)
    assert g.net_energy == 30
    assert g.surplus == 30
    assert g.deficit == 0

def test_deficit_balance():
    g = Microgrid("B", 40, 65)
    assert g.net_energy == -25
    assert g.surplus == 0
    assert g.deficit == 25

def test_invalid_negative_input():
    with pytest.raises(ValueError):
        Microgrid("A", -1, 10)
