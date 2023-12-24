import ngiri


def test_all_imports_are_exported() -> None:
    included_private_members = ["__description__", "__title__", "__version__"]
    assert ngiri.__all__ == sorted(
        (
            member
            for member in vars(ngiri).keys()
            if not member.startswith("_") or member in included_private_members
        ),
        key=str.casefold,
    )
