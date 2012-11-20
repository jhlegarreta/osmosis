import numpy as np

try:
    from mayavi import mlab as maya
    import mayavi.tools as maya_tools
    # Monkey patch away the blocking UI show
    maya.show = lambda: None 

except ImportError:
    e_s = "You can't use 3d visualization functions, "
    e_s += "unless you have mayavi installed."
    raise ValueError(e_s)

from dipy.core.subdivide_octahedron import create_unit_sphere
import dipy.core.geometry as geo
from dipy.core.sphere import Sphere, interp_rbf

import osmosis.tensor as ozt


def _display_maya_voxel(x_plot, y_plot, z_plot, faces, scalars, cmap='jet',
                   colorbar=False, figure=None, vmin=None, vmax=None,
                   file_name=None, azimuth=90, elevation=90):
    """
    Helper function to show data from a voxel in a mayavi figure
    """
        
    if figure is None:
        figure = maya.figure()
    else:
        figure = figure

    # Take care of the color-map:
    if vmin is None:
        vmin = np.min(scalars)
    if vmax is None:
        vmax = np.max(scalars)

    tm = maya.triangular_mesh(x_plot, y_plot, z_plot, faces, scalars=scalars,
                              colormap=cmap, figure=figure, vmin=vmin,
                              vmax=vmax)
    if colorbar:
        maya.colorbar(tm, orientation='vertical')


    scene = figure.scene
    scene.background = (1,1,1)
    scene.parallel_projection=True
    scene.light_manager.light_mode = 'vtk'
    
    # Set it to be aligned along the negative dimension of the y axis: 
    #scene.y_minus_view()

    maya.view(azimuth=azimuth, elevation=elevation)
    
    module_manager = tm.parent
    module_manager.scalar_lut_manager.number_of_labels = 6
    
    scene.render()
    if file_name is not None:
        scene.save(file_name)

    return figure


def plot_tensor_3d(Tensor, cmap='jet', mode='ADC', file_name=None,
                   colorbar=False, figure=None, vmin=None, vmax=None, offset=0,
                   azimuth=90, elevation=90):

    """

    mode: either "ADC", "ellipse" or "pred_sig"

    """
    
    Q = Tensor.Q
    sphere = create_unit_sphere(5)
    vertices = sphere.vertices
    faces = sphere.faces
    x,y,z = vertices.T 

    new_bvecs = np.vstack([x.ravel(), y.ravel(), z.ravel()])
    Tensor = ozt.Tensor(Q, new_bvecs,
                        Tensor.bvals[0] * np.ones(new_bvecs.shape[-1]))

    if mode == 'ADC':
        v = Tensor.ADC
    elif mode == 'ellipse':
        v = Tensor.diffusion_distance
    elif mode == 'pred_sig':
        v = Tensor.predicted_signal(1)

    r, phi, theta = geo.cart2sphere(x,y,z)
    x_plot, y_plot, z_plot = geo.sphere2cart(v, phi, theta)

    # Call and return straightaway:
    return _display_maya_voxel(x_plot, y_plot, z_plot+offset, faces, v,
                               cmap=cmap, colorbar=colorbar, figure=figure,
                               vmin=vmin, vmax=vmax, file_name=file_name,
                               azimuth=azimuth, elevation=elevation)
    


def plot_signal_interp(bvecs, signal, maya=True, cmap='jet', file_name=None,
                        colorbar=False, figure=None, vmin=None, vmax=None,
                        offset=0, azimuth=90, elevation=90):

    """

    Interpolate a measured signal, using RBF interpolation.

    Parameters
    ----------
    signal:

    bvecs: array (3,n)
        the x,y,z locations where the signal was measured 

    offset : float
        where to place the plotted voxel (on the z axis)

    
    """

    s0 = Sphere(xyz=bvecs.T)
    s1 = create_unit_sphere(7)

    interp_signal = interp_rbf(signal, s0, s1)
    interp_signal[interp_signal<0] = 0 
    vertices = s1.vertices
    
    faces = s1.faces
    x,y,z = vertices.T 

    r, phi, theta = geo.cart2sphere(x,y,z)
    x_plot, y_plot, z_plot = geo.sphere2cart(interp_signal, phi, theta)


    # Call and return straightaway:
    return _display_maya_voxel(x_plot, y_plot, z_plot+offset, faces,
                               interp_signal,
                               cmap=cmap, colorbar=colorbar, figure=figure,
                               vmin=vmin, vmax=vmax, file_name=file_name,
                               azimuth=azimuth, elevation=elevation)



def plot_signal(bvecs, signal, maya=True, cmap='jet', file_name=None,
                        colorbar=False, figure=None, vmin=None, vmax=None,
                        offset=0, azimuth=90, elevation=90):

    """

    Interpolate a measured signal, using RBF interpolation.

    Parameters
    ----------
    signal:

    bvecs: array (3,n)
        the x,y,z locations where the signal was measured 

    offset : float
        where to place the plotted voxel (on the z axis)

    
    """

    s0 = Sphere(xyz=bvecs.T)
    vertices = s0.vertices    
    faces = s0.faces
    x,y,z = vertices.T 

    r, phi, theta = geo.cart2sphere(x,y,z)
    x_plot, y_plot, z_plot = geo.sphere2cart(signal, phi, theta)


    # Call and return straightaway:
    return _display_maya_voxel(x_plot, y_plot, z_plot+offset, faces,
                               signal,
                               cmap=cmap, colorbar=colorbar, figure=figure,
                               vmin=vmin, vmax=vmax, file_name=file_name,
                               azimuth=azimuth, elevation=elevation)



def plot_odf_interp(bvecs, odf, maya=True, cmap='jet', file_name=None,
                    colorbar=False, figure=None, vmin=None, vmax=None,
                    offset=0, azimuth=90, elevation=90):
    """
    Plot an interpolated odf, while making sure to mirror reflect it, due to
    the symmetry of all things diffusion. 

    """
    bvecs_new = np.hstack([bvecs, -bvecs])
    new_odf = np.hstack([odf, odf])
        
    # In the end we call out to plot_signal_interp, which does the job with
    # this shiny new signal/bvecs: 
    return plot_signal_interp(bvecs_new, new_odf,
                        maya=maya, cmap=cmap, file_name=file_name,
                        colorbar=colorbar, figure=figure, vmin=vmin, vmax=vmax,
                        offset=offset, azimuth=azimuth, elevation=elevation)

def plot_cut_planes(vol,
                    overlay=None,
                    slice_coronal=None,
                    slice_saggital=None,
                    slice_axial=None,
                    outline=False,
                    cmap='gray',
                    overlay_cmap='jet',
                    invert_cmap=False,
                    vmin=None,
                    vmax=None,
                    figure=None,
                    view_azim=45.0,
                    view_elev=45.0,
                    file_name=None):
    """
    Display cut planes into a volume

    Parameters
    ----------
    vol: 3D array

    overlay: 3D array, optional
        This will be laid on top of the volume as a second layer (you might
        want to have a lot of nan's in there...).

    n_planes: int, optional
       How many planes to show (default: 2)

    outline: bool, optional
       Whether to add a box outline for each plane.

    cmap: str, optional
       The name of a mayavi colormap to use (default: 'gray')
    """ 

    if figure is None:
        figure = maya.figure()    
    else:
        figure = figure

    # Count yer slices as an indication for how many planes are needed: 
    n_planes = len(np.where(np.array([slice_coronal,
                                      slice_axial,
                                      slice_saggital]))[0])
    
    planes = []
    translator = dict(x_axes = slice_saggital,
                      y_axes = slice_coronal,
                      z_axes = slice_axial)

    oris = ['x_axes', 'y_axes', 'z_axes']
    for i in range(n_planes):
        # So that you can return all of them: 
        planes.append(
            maya.pipeline.image_plane_widget(
                maya.pipeline.scalar_field(vol),
                plane_orientation=oris[i],
                slice_index=translator[oris[i]],
                transparent=True,
                colormap=cmap
                )
                )

    # We'll want to set an alpha of 0 for nans if those exist: 
    nans_exist = False
    if overlay is not None:
        if np.any(np.isnan(overlay)):
            nans_exist = True
            
        overlay_planes = []
        for i in range(n_planes):
            overlay_planes.append(maya.pipeline.image_plane_widget(
                maya.pipeline.scalar_field(overlay),
                plane_orientation=oris[i],
                slice_index=translator[oris[i]],
                colormap=overlay_cmap,
                vmin=vmin,
                vmax=vmax))

    if outline: 
        maya.outline()

    scene = figure.scene
    scene.background = (0.7529411764705882,
                        0.7529411764705882,
                        0.7529411764705882)

    # If there are nan values in there, we want to make sure that they get an
    # alpha value of 0:
    for op in overlay_planes:
        module_manager = op.parent
        module_manager.scalar_lut_manager.reverse_lut = invert_cmap
        if nans_exist:
            lut = module_manager.scalar_lut_manager.lut.table.to_array()
            lut[0, -1] = 0
            module_manager.scalar_lut_manager.lut.table = lut

    maya.view(view_azim, view_elev)

    scene.render()
    
    scene = figure.scene
    if file_name is not None:
        scene.save(file_name)

    return figure
    