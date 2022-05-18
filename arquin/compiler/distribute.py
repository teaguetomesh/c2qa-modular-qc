import subprocess


def distribute(source_fname: str, target_fname: str) -> None:
    subprocess.call(
        [
            "/home/weit/scotch/build/bin/gmap",
            f"workspace/{source_fname}_source.txt",
            f"workspace/{target_fname}_target.txt",
            f"workspace/{source_fname}_{target_fname}_distribution.txt",
        ]
    )
