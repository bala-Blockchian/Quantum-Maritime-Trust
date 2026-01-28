use dep::std;

fn main(
    sulphur_content: Field,           // Private
    threshold: pub Field,             // Public Input 0
    salt: Field                       // Private
) -> pub Field {                      // Public Input 1 (The Return Value)
    // 1. Safety Check
    assert(sulphur_content as u32 <= threshold as u32);

    // 2. Generate a commitment (hash) to "lock" this proof to a specific value
    // This return value automatically becomes the second element in the publicInputs array
    let commitment = std::hash::poseidon::hash([sulphur_content, salt]);
    
    commitment
}