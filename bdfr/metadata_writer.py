#!/usr/bin/env python3

import logging
import re
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class MetadataWriter:
    def __init__(self, exiftool_path: str = "exiftool", exiftool_config: Optional[str] = None) -> None:
        self.exiftool_path = exiftool_path
        self.exiftool_config = exiftool_config
        if self.exiftool_config and not Path(self.exiftool_config).exists():
            logger.warning(f"Exiftool config not found: {self.exiftool_config}")

    @staticmethod
    def _sanitize_like_filename(value: str) -> str:
        # Mirror downloader script filename cleanup:
        # 1) spaces -> underscores
        # 2) keep only [-()A-Za-z0-9_.]
        out = value.replace(" ", "_")
        out = re.sub(r"[^-()A-Za-z0-9_.]+", "", out)
        return out

    def write_reddit_tags(
        self,
        file_path: Path,
        user: str,
        title: str,
        post_id: str,
        votes: Optional[int],
        subreddit: Optional[str] = None,
        gallery_index: Optional[int] = None,
        write_title: bool = False,
    ) -> bool:
        user_clean = self._sanitize_like_filename(user)
        title_clean = self._sanitize_like_filename(title)
        subreddit_clean = self._sanitize_like_filename(subreddit) if subreddit else ""

        cmd = [
            self.exiftool_path,
        ]
        if self.exiftool_config:
            cmd.extend(["-config", self.exiftool_config])
        cmd.extend(
            [
                "-overwrite_original_in_place",
                "-P",
            ]
        )

        cmd.extend(
            [
                f"-XMP-Reddit:RedditUser={user_clean}",
                f"-XMP-Reddit:RedditTitle={title_clean}",
                f"-XMP-Reddit:RedditPostID={post_id}",
            ]
        )
        if subreddit_clean:
            cmd.append(f"-XMP-Reddit:RedditSubreddit={subreddit_clean}")

        if votes is not None:
            cmd.append(f"-XMP-Reddit:RedditVotes={votes}")
        if gallery_index is not None:
            cmd.append(f"-XMP-Reddit:RedditGalleryIndex={gallery_index}")
        if write_title:
            cmd.append(f"-Title={user_clean}_{title_clean}")

        cmd.append(str(file_path))

        try:
            proc = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            stderr_txt = (proc.stderr or "").strip()
            # exiftool may return 0 while still emitting warnings (e.g. unknown tags)
            if stderr_txt:
                logger.warning(f"Metadata write warning for {file_path}: {stderr_txt}")
                return False
            return True
        except (OSError, subprocess.CalledProcessError) as e:
            logger.warning(f"Failed writing metadata for {file_path}: {e}")
            return False
