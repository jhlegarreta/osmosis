
# Lines above this one are auto-generated by the wrapper to provide as params:
# i
import time
import osmosis.model.dti as dti
import osmosis.predict_n_cleaned as pn
from osmosis.utils import separate_bvals
import nibabel as nib
import os
import numpy as np

if __name__=="__main__":
    t1 = time.time()
    data_path = "/biac4/wandell/data/klchan13/100307/Diffusion/data"
    
    data_file = nib.load(os.path.join(data_path, "data.nii.gz"))
    wm_data_file = nib.load(os.path.join(data_path,"wm_mask_registered.nii.gz"))
    
    data = data_file.get_data()
    wm_data = wm_data_file.get_data()
    wm_idx = np.where(wm_data==1)
    
    bvals = np.loadtxt(os.path.join(data_path, "bvals"))
    bvecs = np.loadtxt(os.path.join(data_path, "bvecs"))
    
    low = i*200
    # Make sure not to go over the edge of the mask:
    high = np.min([(i+1) * 200, int(np.sum(wm_data))])

    # Now set the mask:
    mask = np.zeros(wm_data_file.shape)
    mask[wm_idx[0][low:high], wm_idx[1][low:high], wm_idx[2][low:high]] = 1

    # Predict 10% (n = 10)
    ad = {1000:1.6386920952169737, 2000:1.2919249903637751, 3000:0.99962593218241236}
    rd = {1000:0.33450124887561905, 2000:0.28377379537043729, 3000:0.24611723207420028}
    
    cc_list_single = pn.predict_n(data, bvals, bvecs, mask, ad, rd, 10, "single",
                                  mean = "mean_model", sph_cc = True, solver = "nnls")
    np.save("cc_single%s.npy"%i, cc_list_single[0])
    cc_list_multi = pn.predict_n(data, bvals, bvecs, mask, ad, rd, 10, "multi",
                                 mean = "mean_model", sph_cc = True, solver = "nnls")
    np.save("cc_b1k_multi%s.npy"%i, cc_list_multi[0])
    np.save("cc_b2k_multi%s.npy"%i, cc_list_multi[1])
    np.save("cc_b3k_multi%s.npy"%i, cc_list_multi[2])

    t2 = time.time()
    print "This program took %4.2f minutes to run."%((t2 - t1)/60.)
