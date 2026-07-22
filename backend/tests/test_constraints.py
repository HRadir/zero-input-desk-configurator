import json
from pathlib import Path

import pytest

from app.constraints.engine import validate_config

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture(scope="module")
def catalogue():
    with open(DATA_DIR / "catalogue.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def contraintes():
    with open(DATA_DIR / "contraintes.json", encoding="utf-8") as f:
        return json.load(f)


def rule_ids(issues):
    return {issue.rule_id for issue in issues}


def test_config_valide_scandinave_2_ecrans(catalogue, contraintes):
    config = {
        "finition_id": "finition_chene_clair",
        "plateau_id": "plateau_standard",
        "largeur_choisie_cm": 140,
        "structure_id": "structure_double_moteur",
        "nombre_ecrans": 2,
        "accessoires": ["bras_ecran_double", "passe_cable"],
        "style_demande": "scandinave",
    }
    result = validate_config(config, catalogue, contraintes)
    assert result.valid is True
    assert result.errors == []
    assert result.warnings == []


def test_reference_inconnue(catalogue, contraintes):
    config = {
        "finition_id": "finition_chene_clair",
        "plateau_id": "plateau_inexistant",
        "largeur_choisie_cm": 140,
        "structure_id": "structure_double_moteur",
        "nombre_ecrans": 1,
        "accessoires": [],
    }
    result = validate_config(config, catalogue, contraintes)
    assert result.valid is False
    assert "reference_inconnue" in rule_ids(result.errors)


def test_largeur_min_selon_ecrans(catalogue, contraintes):
    config = {
        "finition_id": "finition_chene_clair",
        "plateau_id": "plateau_standard",
        "largeur_choisie_cm": 120,
        "structure_id": "structure_double_moteur",
        "nombre_ecrans": 2,
        "accessoires": [],
    }
    result = validate_config(config, catalogue, contraintes)
    assert result.valid is False
    assert "largeur_min_selon_ecrans" in rule_ids(result.errors)


def test_moteur_triple_requis_si_largeur(catalogue, contraintes):
    config = {
        "finition_id": "finition_chene_fonce",
        "plateau_id": "plateau_large",
        "largeur_choisie_cm": 200,
        "structure_id": "structure_double_moteur",
        "nombre_ecrans": 3,
        "accessoires": [],
    }
    result = validate_config(config, catalogue, contraintes)
    assert result.valid is False
    assert "moteur_triple_requis_si_largeur" in rule_ids(result.errors)


def test_structure_largeur_max_compatible(catalogue, contraintes):
    config = {
        "finition_id": "finition_chene_fonce",
        "plateau_id": "plateau_large",
        "largeur_choisie_cm": 200,
        "structure_id": "structure_double_moteur",
        "nombre_ecrans": 3,
        "accessoires": [],
    }
    result = validate_config(config, catalogue, contraintes)
    assert result.valid is False
    assert "structure_largeur_max_compatible" in rule_ids(result.errors)


def test_bras_double_profondeur_min(catalogue, contraintes):
    config = {
        "finition_id": "finition_blanc",
        "plateau_id": "plateau_compact",
        "largeur_choisie_cm": 120,
        "structure_id": "structure_double_moteur",
        "nombre_ecrans": 2,
        "accessoires": ["bras_ecran_double"],
    }
    result = validate_config(config, catalogue, contraintes)
    assert result.valid is False
    assert "bras_double_profondeur_min" in rule_ids(result.errors)


def test_panneau_acoustique_largeur_min(catalogue, contraintes):
    config = {
        "finition_id": "finition_chene_clair",
        "plateau_id": "plateau_standard",
        "largeur_choisie_cm": 120,
        "structure_id": "structure_double_moteur",
        "nombre_ecrans": 1,
        "accessoires": ["panneau_acoustique"],
    }
    result = validate_config(config, catalogue, contraintes)
    assert result.valid is False
    assert "panneau_acoustique_largeur_min" in rule_ids(result.errors)


def test_dock_requiert_passe_cable(catalogue, contraintes):
    config = {
        "finition_id": "finition_chene_clair",
        "plateau_id": "plateau_standard",
        "largeur_choisie_cm": 140,
        "structure_id": "structure_double_moteur",
        "nombre_ecrans": 1,
        "accessoires": ["dock_usb"],
    }
    result = validate_config(config, catalogue, contraintes)
    assert result.valid is False
    assert "dock_requiert_passe_cable" in rule_ids(result.errors)


def test_bras_ecran_correspond_nombre_ecrans(catalogue, contraintes):
    config = {
        "finition_id": "finition_chene_clair",
        "plateau_id": "plateau_standard",
        "largeur_choisie_cm": 140,
        "structure_id": "structure_double_moteur",
        "nombre_ecrans": 2,
        "accessoires": ["bras_ecran_simple"],
    }
    result = validate_config(config, catalogue, contraintes)
    assert result.valid is False
    assert "bras_ecran_correspond_nombre_ecrans" in rule_ids(result.errors)


def test_finition_style_coherence_avertissement_non_bloquant(catalogue, contraintes):
    config = {
        "finition_id": "finition_chene_clair",
        "plateau_id": "plateau_standard",
        "largeur_choisie_cm": 140,
        "structure_id": "structure_double_moteur",
        "nombre_ecrans": 2,
        "accessoires": ["bras_ecran_double", "passe_cable"],
        "style_demande": "industriel",
    }
    result = validate_config(config, catalogue, contraintes)
    assert result.valid is True
    assert result.errors == []
    assert "finition_style_coherence" in rule_ids(result.warnings)
