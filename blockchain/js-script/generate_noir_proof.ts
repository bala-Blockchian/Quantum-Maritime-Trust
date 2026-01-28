import { Barretenberg, Fr, UltraHonkBackend } from "@aztec/bb.js";
import { ethers } from "ethers";

import { Noir } from "@noir-lang/noir_js";
import path from 'path';
import fs from 'fs';

const circuitPath = path.resolve(__dirname, '../target/circuits.json');
const circuit = JSON.parse(fs.readFileSync(circuitPath, 'utf8'));

export default async function generateMaritimeProof() {
    const args = process.argv.slice(2);
    
    if (args.length < 3) {
        throw new Error("Missing arguments: Expected [sulphur_content, threshold, salt]");
    }

    const sulphur_content = args[0];
    const threshold = args[1];
    const salt = args[2];

    try {
        const noir = new Noir(circuit);
        const honk = new UltraHonkBackend(circuit.bytecode, { threads: 1 });

        const input = {
            sulphur_content: sulphur_content,
            threshold: threshold,
            salt: salt
        };

        const { witness } = await noir.execute(input);
        const originalLog = console.log;
        console.log = () => {};
        const { proof, publicInputs } = await honk.generateProof(witness, { keccak: true });
        console.log = originalLog;

        const result = ethers.AbiCoder.defaultAbiCoder().encode(
            ["bytes", "bytes32[]"],
            [proof, publicInputs]
        );

        return result;
    } catch (error) {
        console.error("Proof Generation Error:", error);
        throw error;
    }
}

(async () => {
    generateMaritimeProof()
        .then((result) => {
            process.stdout.write(result);
            process.exit(0);
        })
        .catch((error) => {
            process.exit(1);
        });
})();