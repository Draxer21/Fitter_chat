import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";

const usernamePattern = /^[a-zA-Z0-9_-]{3,32}$/;
const normalize = (value) => (value || "").trim();

export default function NicknamePrompt({
  visible,
  title,
  description,
  placeholder,
  submitLabel,
  skipLabel,
  validationMessage,
  errorMessage,
  onSuccess,
  onSkip,
}) {
  const { user, updateUsername } = useAuth();
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const shouldShow = Boolean(user?.needs_username) && (visible ?? true);

  useEffect(() => {
    if (!shouldShow) {
      setNickname("");
      setError("");
      setSaving(false);
    }
  }, [shouldShow]);

  if (!shouldShow) {
    return null;
  }

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    const normalized = normalize(nickname).toLowerCase();
    if (!usernamePattern.test(normalized)) {
      setError(validationMessage);
      return;
    }
    try {
      setSaving(true);
      const updated = await updateUsername(normalized);
      setNickname("");
      onSuccess?.(updated);
    } catch (err) {
      setError(err?.message || errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleSkip = () => {
    onSkip?.();
  };

  return (
    <section className="alert alert-info mt-4" role="dialog" aria-live="polite">
      <div className="mb-3">
        <h5 className="mb-1">{title}</h5>
        <p className="mb-0">{description}</p>
      </div>
      <form onSubmit={handleSubmit} className="d-flex flex-column gap-2">
        <label htmlFor="nicknameInput" className="form-label fw-semibold">
          {placeholder}
        </label>
        <input
          id="nicknameInput"
          className="form-control"
          value={nickname}
          onChange={(event) => setNickname(event.target.value)}
          placeholder={placeholder}
          autoComplete="nickname"
          disabled={saving}
          required
        />
        {error && (
          <div className="text-danger small" role="alert">
            {error}
          </div>
        )}
        <div className="d-flex flex-wrap gap-2 mt-2">
          <button type="submit" className="btn btn-dark" disabled={saving}>
            {saving ? `${submitLabel}...` : submitLabel}
          </button>
          {onSkip && (
            <button type="button" className="btn btn-outline-secondary" onClick={handleSkip} disabled={saving}>
              {skipLabel}
            </button>
          )}
        </div>
      </form>
    </section>
  );
}
