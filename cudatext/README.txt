cudatext/ — STATghost host for CudaText (VP-EB-1 + EB-1b + workbar)
==================================================================

cuda_statghost/  send selection / complete statement; Toggle Arm/Idle
                 (`#. STATGHOST:<CMD>` clipboard contract — protocol.py
                 twin of STATghost src/ubridgecmd.pas).
                 Native chrome: toolbar + side tab (chrome.py).
                 Config UI: path to the STATghost executable
                 (settings/cuda_statghost.ini). Auto-detect uses
                 realpath so a symlink install still finds the sibling
                 clone.

The folder name `cuda_statghost` is required by CudaText (`py/` +
install.inf subdir). The student menu caption is **STATghost**.

Universal identity (menu / workbar / protocol): `../shared/README.txt`.

Lab Linux (portable CudaText sibling):
  bash cudatext/install_lab.sh
  # or: CUDA_ROOT=/path/to/CudaText bash cudatext/install_lab.sh

Then restart CudaText. STATghost must be running and Armed for eval.

Do not embed STATghost Console|Plot|Explorer UI here (D29).
