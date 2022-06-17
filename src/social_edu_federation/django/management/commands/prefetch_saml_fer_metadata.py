"""This management command runs metadata stores cache update."""
from django.core.management import BaseCommand, CommandError

from social_django.utils import load_backend, load_strategy


class Command(BaseCommand):
    """Call metadata store fetch command, resulting in a cache data update."""

    help = 'Update RENATER\'s "Féderation Éducation-Recherche" (FER) federation metadata cache.'

    def add_arguments(self, parser):
        parser.add_argument("backends", nargs="+", type=str)

    def handle(self, *args, **options):
        """
        Execute management command: we use the metadata store to retrieve the
        parsed metadata and store them in cache.

        The metadata store must provide a `refresh_cache_entries` method otherwise
        the command fails.

        We catch any error to allow the command to run the cache refresh on other
        backends provided in arguments even if one backend fails (e.g. for a timeout
        reason).
        """
        success = True
        for backend_name in options["backends"]:
            if options["verbosity"] >= 1:
                self.stdout.write(f"Refreshing metadata for backend '{backend_name}'")

            strategy = load_strategy()
            backend = load_backend(strategy, backend_name, redirect_uri=None)
            metadata_store = backend.get_metadata_store()

            try:
                metadata_store.refresh_cache_entries()
            except (NotImplementedError, AttributeError) as exception:
                success = False
                self.stderr.write(
                    f"{metadata_store.__class__.__name__} does not provide way "
                    f"to refresh the metadata cache ({exception.__class__.__name__})"
                )
            except Exception as exception:  # pylint: disable=broad-except
                success = False
                self.stderr.write(
                    f"{metadata_store.__class__.__name__} failed "
                    f"to refresh the metadata cache ({exception})"
                )

        if not success:
            raise CommandError(
                "Something went wrong with `prefetch_saml_fer_metadata` command, "
                "please check your logs."
            )
        self.stdout.write("All metadata caches refreshed")
