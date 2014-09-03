# Lines above this one are auto-generated by the wrapper to provide as params:
# i
"""

"""

import os
import numpy as np
import nibabel as nib
import numpy.matlib as matlab
import dipy.core.gradients as grad
import dipy.reconst.dsi as dsi
import dipy.reconst.dti as dti
from dipy.viz import fvtk
from dipy.data import get_sphere
import dipy.segment.mask as dpm

import osmosis.model.isotropic as mdm
import osmosis.utils as ozu
import time

if __name__=="__main__":
    t1 = time.time()

    data_path = "/biac4/wandell/data/qytian/DSIProject/"

    DSI515_bx = nib.load(data_path +
                         "DSI515/DSI515_bx_reg.nii.gz").get_data()
    DSI515_b0 = nib.load(data_path +
                         "DSI515/DSI515_b0_reg.nii.gz").get_data().mean(-1)

    DSI515 = np.concatenate([DSI515_b0[..., None], DSI515_bx], axis=-1)

    DSI515_gtab = grad.gradient_table(data_path + "DSI515/bvals_515_standard.txt", data_path + "DSI515/bvecs_prs_515_standard.txt")

    models = [mdm.single_exp_rs, mdm.bi_exp_rs, mdm.single_exp_nf_rs]
    labels = ["mono-exponential", "bi-exponential", "mono-exponential + noise"]
    
    DSI515_mask = nib.load(data_path +
                           "/DSI515/mask_mask_hand.nii.gz").get_data()

    wm_idx = np.where(DSI515_mask==1)

    low = i*10
    # Make sure not to go over the edge of the mask:
    high = np.min([(i+1) * 10, int(np.sum(DSI515_mask))])

    # Set the part of the mask to use here 
    mask = np.zeros(DSI515_mask.shape)
    mask[wm_idx[0][low:high], wm_idx[1][low:high], wm_idx[2][low:high]] = 1

    data_name = os.path.join(data_path, "xval", "DSI515_%i_"%i)

    for isotropic_model, label in zip(models, labels):
        print("Fitting %s"%label)
        fname_params = os.path.join(data_name, label, "-params-wm.npy")
        fname_predictions = os.path.join(data_name, label, "-predictions-wm.npy")
        param_out, fit_out, _ = mdm.isotropic_params(DSI515,
                                                     DSI515_gtab.bvals,
                                                     DSI515_gtab.bvecs,
                                                     mask,
                                                     isotropic_model,
                                                signal = "relative_signal")
        np.save(fname_params, param_out)
        _, this_predict = mdm.kfold_xval_MD_mod(DSI515,
                                                DSI515_gtab.bvals,
                                                DSI515_gtab.bvecs.T,
                                                mask,
                                                isotropic_model,
                                                10,
                                                signal = "relative_signal")
        np.save(fname_predictions, this_predict)
        
    t2 = time.time()
    print "This program took %4.2f minutes to run."%((t2 - t1)/60.)
