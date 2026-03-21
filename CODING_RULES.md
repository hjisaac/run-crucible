# CODING_RULES.md

## Coding Standards

- All code must follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) for formatting, naming, and documentation.
- Code must be written as if by a senior software engineer: prioritize simplicity, clarity, and robustness.
- Avoid unnecessary complexity and ugly or convoluted solutions.
- Write clear, concise docstrings and comments where they add value, but do not over-comment trivial code.
- Add contextual comments or documentation when it will help future developers quickly understand non-obvious logic or design decisions.
- All public functions, classes, and modules should have docstrings explaining their purpose and usage.
- Prefer explicit, readable code over clever or obscure tricks.
- Tests and examples should be easy to read and maintain.

## Modification Rules for AI

- The AI must always respect these coding rules when making modifications.
- The AI should never propose code that is overly complex, hard to maintain, or deviates from the Google Style Guide without strong justification.
- The AI should always add context or rationale in comments when it helps future developers.
- The AI should avoid excessive or redundant comments and documentation.
- The AI should always strive for code that is simple, robust, and easy to understand.
- The AI must place imports at the top of the file. In-function (mid-body) imports are not allowed unless absolutely critical (e.g., to avoid circular imports or for performance reasons with clear justification), and in such cases, a human must approve it first.

