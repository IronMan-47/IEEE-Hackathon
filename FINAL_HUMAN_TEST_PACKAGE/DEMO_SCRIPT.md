# JARVIS - Human Testing Demo Script

This script is meant to guide a non-developer through evaluating the Windows native execution path using the isolated `/demo` directory. 

## 1. Preparation
1. Open `FINAL_HUMAN_TEST_PACKAGE/demo` in VS Code.
2. Launch the JARVIS application normally.
3. Keep VS Code and JARVIS side-by-side.

## 2. Hello World Generation
1. In the JARVIS input box, type: `Create a python hello world script here.`
2. Wait for JARVIS to detect the VS Code context.
3. Review the generated proposal in the overlay.
4. Click **APPROVE**.
5. Observe the file being safely created in the `/demo` directory.

## 3. The Rejection Test
1. Type: `Delete the entire demo directory.`
2. Wait for the proposal to populate.
3. Click **REJECT**.
4. Confirm no files are touched and the execution pipeline aborts.

## 4. The Modification Test
1. Type: `Create a new file named test1.txt`
2. Wait for the proposal.
3. Click **MODIFY**. Change the filename in the JSON preview to `test_modified.txt`.
4. Click **APPROVE**.
5. Verify `test_modified.txt` was created instead.

## 5. The Emergency Stop Test
1. Request a long-running execution or a multi-step generation task.
2. The moment it begins executing, press **Ctrl+Shift+Escape** (Global Emergency Stop).
3. Confirm the UI flashes Red and indicates `SAFE_STOPPED`.
4. Check the demo folder to ensure the execution immediately halted mid-way.

## Note to Tester
**DO NOT use this demo to test outside the isolated `/demo` directory.** JARVIS has restricted OS automation capabilities for this release, but it is best practice to keep mock modifications sandboxed during Beta validation.
