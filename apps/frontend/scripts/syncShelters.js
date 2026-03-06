import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const src = path.resolve(__dirname, "../../../routing/artifacts/pj_shelters.csv");
const dest = path.resolve(__dirname, "../public/pj_shelters.csv");

if (fs.existsSync(src)) {
  fs.copyFileSync(src, dest);
  console.log("Shelter CSV synced.");
} else {
  console.log("Warning: routing/artifacts/pj_shelters.csv not found.");
}