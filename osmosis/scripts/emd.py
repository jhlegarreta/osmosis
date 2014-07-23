# A script for running EMD calculations from the terminal
# Lines above this one are auto-generated by the wrapper to provide as params:
# i, sid, fODF, im, data_path
import time
import osmosis.model.dti as dti
import osmosis.predict_n as pn
from osmosis.utils import separate_bvals
import nibabel as nib
import os
import numpy as np

#sid_list = ["103414", "105115", "110411", "111312", "113619",
#            "115320", "117122", "118730", "118932"]
sid="117122"
data_path = os.path.join("/biac4/wandell/data/klchan13/hcp_data_q3/%s/T1w/Diffusion/"%sid)
data_save_path = os.path.join("/biac4/wandell/data/klchan13/hcp_data_q3/%s/T1w/Diffusion/file_pieces"%sid)

wm_data_file = nib.load(os.path.join(data_path,"wm_mask_no_vent.nii.gz"))
wm_vox_num = np.sum(wm_data_file.get_data().astype(int))

# For dividing up data
emd_file_num = int(np.ceil(wm_vox_num/2000.))
fODF="single"
im="bi_exp_rs"

for i in np.arange(emd_file_num):
    t1 = time.time()
    
    data_file = nib.load(os.path.join(data_path, "data.nii.gz"))
    wm_data_file = nib.load(os.path.join(data_path,"wm_mask_no_vent.nii.gz"))
    
    data = data_file.get_data()
    wm_data = wm_data_file.get_data().astype(int)
    wm_idx = np.where(wm_data==1)
    
    bvals = np.loadtxt(os.path.join(data_path, "bvals"))
    bvecs = np.loadtxt(os.path.join(data_path, "bvecs"))
    
    low = i*2000
    # Make sure not to go over the edge of the mask:
    high = np.min([(i+1) * 2000, int(np.sum(wm_data))])
    
    # Now set the mask:
    mask = np.zeros(wm_data_file.shape)
    mask[wm_idx[0][low:high], wm_idx[1][low:high], wm_idx[2][low:high]] = 1
    
    # Load the AD, RD values for this subject.
    ad_rd = np.loadtxt(os.path.join(data_path, "ad_rd_%s.txt"%sid))
    ad = {1000:ad_rd[0,0], 2000:ad_rd[0,1], 3000:ad_rd[0,2]}
    rd = {1000:ad_rd[1,0], 2000:ad_rd[1,1], 3000:ad_rd[1,2]}
    
    if fODF == "multi":
        precision = "emd_multi_combine"
    else:
        precision = "emd"
    
    if im == "bi_exp_rs":
        shorthand_im = "be"
    elif im == "single_exp_rs":
        shorthand_im = "se"
    
    # Predict 10% (n = 10)
    emd = pn.kfold_xval(data, bvals, bvecs, mask, ad, rd, 10, fODF,
                        mean = "mean_model", precision = precision,
                        solver = "nnls", mean_mod_func = im)
                        
    np.save(os.path.join(data_save_path, "emd_%s_%s%s.npy"%(fODF,shorthand_im,i)), emd[0].T)
    
    t2 = time.time()
    print "This program took %4.2f minutes to run."%((t2 - t1)/60.)
