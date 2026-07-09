"""Catalog loading + lookup tests, using a tmp CSV (no network)."""

from app.services.catalog import Catalog


def _write_csv(tmp_path):
    p = tmp_path / "products.csv"
    p.write_text(
        "product_id,name,brand,barcode,category,mrp,weight_g,energy_kcal,protein_g,sugar_g,sodium_mg\n"
        "1,Marie Gold,Britannia,8901063010101,biscuits,30,120,450,7,20,350\n"
        "2,Masala Oats,Saffola,8901234500002,cereal,45,40,380,11,4,600\n",
        encoding="utf-8",
    )
    return p


def test_barcode_lookup(tmp_path):
    cat = Catalog.from_csv(_write_csv(tmp_path))
    p = cat.by_barcode("8901063010101")
    assert p is not None
    assert p.name == "Marie Gold"
    assert p.mrp == 30.0
    assert p.nutrition["protein_g"] == 7


def test_fuzzy_search(tmp_path):
    cat = Catalog.from_csv(_write_csv(tmp_path))
    results = cat.search("saffola oats")
    assert results
    assert results[0].brand == "Saffola"


def test_missing_file_is_empty_not_error(tmp_path):
    cat = Catalog.from_csv(tmp_path / "does_not_exist.csv")
    assert cat.all() == []
    assert cat.by_barcode("x") is None
