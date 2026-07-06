"""Provider-block parser and renderer for shared skill sources.

The source-visible / install-invisible provider tag syntax is intentionally
strict. Malformed, unclosed,
mismatched, unknown-provider, and nested block tags are hard errors and never
cause silent content loss.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Optional


PROVIDERS = ("CLAUDE", "CODEX", "GEMINI")

_BRACKET_TOKEN_RE = re.compile(r"\[([^\]\n]+)\]")
_INLINE_CRITICAL_RE = re.compile(r"^\[(CLAUDE|CODEX|GEMINI)\]\[CRITICAL\]")
# Near-miss form (wrong case): must hard-error, never pass through as content —
# otherwise `[claude][critical]…` ships to EVERY provider as literal text with
# zero diagnostic.
_INLINE_CRITICAL_NEARMISS_RE = re.compile(
    r"^\[(claude|codex|gemini)\]\[critical\]", re.IGNORECASE
)
# Exact tag shape in the wrong case ([shared], [provider:claude], …). Exact
# match only — prose brackets like "[shared skills](#link)" stay content.
_BLOCK_NEARMISS_RE = re.compile(r"^/?(?:SHARED|PROVIDER:[A-Z]+)$", re.IGNORECASE)


class ProviderBlockError(ValueError):
    """Raised when provider block syntax cannot be rendered safely."""


@dataclass(frozen=True)
class Segment:
    """A parsed source segment.

    `provider is None` means shared content; otherwise it is one of PROVIDERS.
    """

    text: str
    provider: Optional[str] = None


@dataclass(frozen=True)
class _Tag:
    closing: bool
    name: str
    provider: Optional[str] = None


def normalize_provider(provider: str) -> str:
    """Return the canonical uppercase provider name or raise."""

    normalized = provider.strip().upper()
    if normalized not in PROVIDERS:
        raise ProviderBlockError(
            f"unknown provider {provider!r}; expected one of {', '.join(PROVIDERS)}"
        )
    return normalized


def parse_provider_blocks(text: str) -> list[Segment]:
    """Parse block tags into shared/provider-scoped segments."""

    segments: list[Segment] = []
    open_tag: Optional[_Tag] = None
    pos = 0

    for match in _BRACKET_TOKEN_RE.finditer(text):
        tag = _classify_block_tag(match.group(1))
        if tag is None:
            continue

        if match.start() > pos:
            segments.append(Segment(text[pos : match.start()], _segment_provider(open_tag)))

        if tag.closing:
            if open_tag is None:
                raise ProviderBlockError(f"closing tag [{match.group(1)}] has no open block")
            if (tag.name, tag.provider) != (open_tag.name, open_tag.provider):
                expected = _format_tag(open_tag, closing=True)
                actual = f"[{match.group(1)}]"
                raise ProviderBlockError(f"mismatched closing tag {actual}; expected {expected}")
            open_tag = None
        else:
            if open_tag is not None:
                raise ProviderBlockError(
                    f"nested block tag [{match.group(1)}] inside {_format_tag(open_tag)}"
                )
            open_tag = tag

        pos = match.end()

    if open_tag is not None:
        raise ProviderBlockError(f"unclosed block tag {_format_tag(open_tag)}")

    if pos < len(text):
        segments.append(Segment(text[pos:], None))

    return _coalesce_segments(segments)


def render_for_provider(text: str, provider: str) -> str:
    """Render source text for one provider, removing all tag scaffolding."""

    target = normalize_provider(provider)
    included = "".join(
        segment.text
        for segment in parse_provider_blocks(text)
        if segment.provider is None or segment.provider == target
    )
    return _filter_inline_critical(included, target)


def source_has_provider_tags(text: str) -> bool:
    """Return True when source text contains block or inline provider tags."""

    try:
        if any(segment.provider is not None for segment in parse_provider_blocks(text)):
            return True
    except ProviderBlockError:
        raise
    return any(_INLINE_CRITICAL_RE.match(line) for line in text.splitlines())


def _segment_provider(open_tag: Optional[_Tag]) -> Optional[str]:
    if open_tag is None or open_tag.name == "SHARED":
        return None
    return open_tag.provider


def _classify_block_tag(raw: str) -> Optional[_Tag]:
    if raw != raw.strip():
        stripped = raw.strip()
        if _looks_like_block_tag(stripped) or _BLOCK_NEARMISS_RE.match(stripped):
            raise ProviderBlockError(f"malformed block tag [{raw}]")
        return None

    if raw == "SHARED":
        return _Tag(False, "SHARED")
    if raw == "/SHARED":
        return _Tag(True, "SHARED")
    if raw.startswith("SHARED") or raw.startswith("/SHARED"):
        raise ProviderBlockError(f"malformed block tag [{raw}]")

    if raw.startswith("PROVIDER") or raw.startswith("/PROVIDER"):
        closing = raw.startswith("/")
        body = raw[1:] if closing else raw
        if not body.startswith("PROVIDER:"):
            raise ProviderBlockError(f"malformed provider block tag [{raw}]")
        provider = body.removeprefix("PROVIDER:")
        # Tag grammar is literal: whitespace or lowercase inside the provider
        # token (e.g. "[PROVIDER: CODEX]", "[PROVIDER:codex]") is malformed,
        # not normalizable; provider literals must be uppercase.
        # normalize_provider stays lenient for CLI args only.
        if not provider or provider != provider.strip() or provider != provider.upper():
            raise ProviderBlockError(f"malformed provider block tag [{raw}]")
        return _Tag(closing, "PROVIDER", normalize_provider(provider))

    # Case near-miss ([shared], [provider:claude], [Provider:CLAUDE]…): a tag in
    # the wrong case is malformed, not content; passing it through would ship
    # it verbatim to every provider render.
    if _BLOCK_NEARMISS_RE.match(raw):
        raise ProviderBlockError(f"malformed block tag [{raw}]")

    return None


def _looks_like_block_tag(raw: str) -> bool:
    return (
        raw == "SHARED"
        or raw == "/SHARED"
        or raw.startswith("SHARED")
        or raw.startswith("/SHARED")
        or raw.startswith("PROVIDER")
        or raw.startswith("/PROVIDER")
    )


def _format_tag(tag: _Tag, closing: bool = False) -> str:
    slash = "/" if closing else ""
    if tag.name == "SHARED":
        return f"[{slash}SHARED]"
    return f"[{slash}PROVIDER:{tag.provider}]"


def _coalesce_segments(segments: Iterable[Segment]) -> list[Segment]:
    coalesced: list[Segment] = []
    for segment in segments:
        if not segment.text:
            continue
        if coalesced and coalesced[-1].provider == segment.provider:
            previous = coalesced[-1]
            coalesced[-1] = Segment(previous.text + segment.text, previous.provider)
        else:
            coalesced.append(segment)
    return coalesced


def _filter_inline_critical(text: str, target: str) -> str:
    rendered: list[str] = []
    for line in text.splitlines(keepends=True):
        body = line[:-1] if line.endswith("\n") else line
        newline = "\n" if line.endswith("\n") else ""
        if body.endswith("\r"):
            body = body[:-1]
            newline = "\r" + newline

        match = _INLINE_CRITICAL_RE.match(body)
        if match is None:
            if _INLINE_CRITICAL_NEARMISS_RE.match(body):
                raise ProviderBlockError(f"malformed inline critical tag: {body[:40]!r}")
            rendered.append(line)
            continue
        if match.group(1) == target:
            rendered.append(body[match.end() :] + newline)
    return "".join(rendered)
