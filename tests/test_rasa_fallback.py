"""
Tests de fallback y NLU (RF8).
Verifica la configuracion del FallbackClassifier de Rasa,
los thresholds y la respuesta ante intents desconocidos.
"""
import os
import pytest
import yaml


CHATBOT_DIR = os.path.join(os.path.dirname(__file__), "..", "Chatbot")
CONFIG_PATH = os.path.join(CHATBOT_DIR, "config.yml")
NLU_PATH = os.path.join(CHATBOT_DIR, "data", "nlu.yml")
DOMAIN_PATH = os.path.join(CHATBOT_DIR, "domain.yml")
RULES_PATH = os.path.join(CHATBOT_DIR, "data", "rules.yml")


@pytest.fixture
def config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def domain():
    with open(DOMAIN_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def nlu():
    with open(NLU_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def rules():
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestFallbackConfig:
    """Verificar que FallbackClassifier esta configurado."""

    def test_pipeline_has_fallback_classifier(self, config):
        pipeline = config.get("pipeline", [])
        names = [c.get("name") for c in pipeline]
        assert "FallbackClassifier" in names, "FallbackClassifier no esta en el pipeline"

    def test_fallback_threshold(self, config):
        pipeline = config.get("pipeline", [])
        fc = next((c for c in pipeline if c.get("name") == "FallbackClassifier"), None)
        assert fc is not None
        threshold = fc.get("threshold", 0)
        assert 0.3 <= threshold <= 0.6, f"Threshold {threshold} fuera de rango razonable (0.3-0.6)"

    def test_ambiguity_threshold(self, config):
        pipeline = config.get("pipeline", [])
        fc = next((c for c in pipeline if c.get("name") == "FallbackClassifier"), None)
        assert fc is not None
        ambiguity = fc.get("ambiguity_threshold", 0)
        assert ambiguity > 0, "ambiguity_threshold debe ser > 0"


class TestRulePolicy:
    """Verificar que RulePolicy tiene fallback configurado."""

    def test_rule_policy_exists(self, config):
        policies = config.get("policies", [])
        names = [p.get("name") for p in policies]
        assert "RulePolicy" in names

    def test_core_fallback_threshold(self, config):
        policies = config.get("policies", [])
        rp = next((p for p in policies if p.get("name") == "RulePolicy"), None)
        assert rp is not None
        threshold = rp.get("core_fallback_threshold", 0)
        assert threshold > 0, "core_fallback_threshold no configurado"

    def test_fallback_action_defined(self, config):
        policies = config.get("policies", [])
        rp = next((p for p in policies if p.get("name") == "RulePolicy"), None)
        assert rp is not None
        action = rp.get("core_fallback_action_name", "")
        assert action, "core_fallback_action_name no definido"

    def test_enable_fallback_prediction(self, config):
        policies = config.get("policies", [])
        rp = next((p for p in policies if p.get("name") == "RulePolicy"), None)
        assert rp is not None
        assert rp.get("enable_fallback_prediction") is True


class TestDomainFallback:
    """Verificar que el domain tiene la respuesta de fallback."""

    def test_utter_fuera_de_alcance_exists(self, domain):
        responses = domain.get("responses", {})
        assert "utter_fuera_de_alcance" in responses, \
            "Respuesta 'utter_fuera_de_alcance' no definida en domain.yml"

    def test_fallback_response_has_text(self, domain):
        responses = domain.get("responses", {})
        fallback = responses.get("utter_fuera_de_alcance", [])
        assert len(fallback) > 0, "utter_fuera_de_alcance no tiene variantes de texto"
        assert any(r.get("text") for r in fallback), "utter_fuera_de_alcance sin texto"

    def test_nlu_fallback_intent_in_domain(self, domain):
        intents = domain.get("intents", [])
        intent_names = []
        for i in intents:
            if isinstance(i, str):
                intent_names.append(i)
            elif isinstance(i, dict):
                intent_names.extend(i.keys())
        assert "nlu_fallback" in intent_names, \
            "Intent 'nlu_fallback' no declarado en domain.yml"


class TestNLUData:
    """Verificar que los datos NLU tienen intents clave."""

    def test_nlu_has_intents(self, nlu):
        nlu_items = nlu.get("nlu", [])
        intents = [item.get("intent") for item in nlu_items if "intent" in item]
        assert len(intents) >= 5, f"Solo hay {len(intents)} intents definidos, se esperan al menos 5"

    def test_lookup_musculo_exists(self, nlu):
        nlu_items = nlu.get("nlu", [])
        lookups = [item.get("lookup") for item in nlu_items if "lookup" in item]
        assert "musculo" in lookups, "Lookup 'musculo' no encontrado en nlu.yml"

    def test_lookup_objetivo_exists(self, nlu):
        nlu_items = nlu.get("nlu", [])
        lookups = [item.get("lookup") for item in nlu_items if "lookup" in item]
        assert "objetivo" in lookups, "Lookup 'objetivo' no encontrado en nlu.yml"

    def test_regex_email_exists(self, nlu):
        nlu_items = nlu.get("nlu", [])
        regexes = [item.get("regex") for item in nlu_items if "regex" in item]
        assert "email" in regexes, "Regex 'email' no encontrado en nlu.yml"


class TestRulesHaveFallback:
    """Verificar que las rules incluyen la regla de fallback."""

    def test_fallback_rule_exists(self, rules):
        rules_list = rules.get("rules", [])
        rule_names = [r.get("rule", "") for r in rules_list]
        has_fallback = any("fallback" in name.lower() or "fuera" in name.lower() for name in rule_names)
        assert has_fallback, "No se encontro una regla de fallback en rules.yml"
