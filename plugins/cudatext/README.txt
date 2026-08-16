plugins/cudatext/ — STATghost host for CudaText (VP-EB-1 + EB-1b + workbar)
=========================================================================

Host-specific (stays here; not at the repo root):
  cuda_statghost/  plugin CODE (CudaText requires this subdir name)
  w_todo/          WORKBAR SAP/CPR (VP-WB-*)
  install_lab.sh   symlink into portable CudaText
  run_tf.sh        unit + functional + production

Glyphs: same set for every host — canonical stash `../../shared/png/`.

The folder name `cuda_statghost` is required by CudaText (`py/` +
install.inf subdir). The student menu caption is **STATghost**.

Universal identity (menu / workbar / protocol): `../../shared/README.txt`.
Parent folder: `../` (`plugins/` — one subfolder per host).

Lab Linux (portable CudaText sibling):
  bash plugins/cudatext/install_lab.sh
  # or: CUDA_ROOT=/path/to/CudaText bash plugins/cudatext/install_lab.sh

Then restart CudaText. STATghost must be running and Armed for eval.

Do not embed STATghost Console|Plot|Explorer UI here (D29).
