import {
  copyFileSync,
  existsSync,
  mkdirSync,
  readdirSync,
  rmSync,
  statSync,
} from "node:fs";
import {
  dirname,
  join,
  resolve,
} from "node:path";
import {
  fileURLToPath,
} from "node:url";

const scriptDirectory = dirname(
  fileURLToPath(import.meta.url),
);

const webRoot = resolve(
  scriptDirectory,
  "..",
);

const repositoryRoot = resolve(
  webRoot,
  "..",
);

const sourceDirectory = join(
  repositoryRoot,
  "data",
  "assets",
  "player_images",
);

const destinationDirectory = join(
  webRoot,
  "public",
  "player-images",
);

if (!existsSync(sourceDirectory)) {
  throw new Error(
    `Player image source directory not found: ${sourceDirectory}`,
  );
}

const files = readdirSync(
  sourceDirectory,
)
  .filter(
    (fileName) =>
      fileName.endsWith(".png"),
  )
  .sort();

if (files.length === 0) {
  throw new Error(
    "No player PNG assets were found.",
  );
}

const invalidFileNames = files.filter(
  (fileName) =>
    !/^\d+\.png$/.test(fileName),
);

if (invalidFileNames.length > 0) {
  throw new Error(
    "Player image filenames must use numeric player IDs: "
      + invalidFileNames
        .slice(0, 10)
        .join(", "),
  );
}

rmSync(
  destinationDirectory,
  {
    recursive: true,
    force: true,
  },
);

mkdirSync(
  destinationDirectory,
  {
    recursive: true,
  },
);

let totalBytes = 0;

for (const fileName of files) {
  const sourcePath = join(
    sourceDirectory,
    fileName,
  );

  const destinationPath = join(
    destinationDirectory,
    fileName,
  );

  copyFileSync(
    sourcePath,
    destinationPath,
  );

  totalBytes += statSync(
    sourcePath,
  ).size;
}

const copiedFiles = readdirSync(
  destinationDirectory,
).filter(
  (fileName) =>
    fileName.endsWith(".png"),
);

if (
  copiedFiles.length
  !== files.length
) {
  throw new Error(
    "Player image sync produced an incomplete destination.",
  );
}

console.log(
  `Synced ${files.length} player images `
    + `(${(totalBytes / 1024 / 1024).toFixed(2)} MiB).`,
);
