import os

import microtrack as mt
import microtrack.fibers as mtf

import numpy as np
import numpy.testing as npt
import numpy.testing.decorators as dec

import scipy.io as sio

def test_Fiber():
    """
    Testing initalization of the Fiber class
    """
    # Providing a list as an input works:
    arr1d = [1,2,3]
    # This is the most basic example possible:
    f1 = mtf.Fiber(arr1d)
    # 2D arrays should be 3 by n:
    arr2d = np.array([[1,2], [3,4],[5,6]])
    # So this is OK:
    f2 = mtf.Fiber(arr2d)    
    # But this raises a ValueError:
    npt.assert_raises(ValueError, mtf.Fiber, arr2d.T)
    # This should also raise (second dim is 4, rather than 3): 
    npt.assert_raises(ValueError, mtf.Fiber, np.empty((10,4)))
    # This should be OK:
    f3 = mtf.Fiber(np.array(arr2d), affine = np.eye(4), fiber_stats=dict(a=1))
    npt.assert_equal(f3.fiber_stats, {'a':1})

def test_Fiber_xform():

    arr2d = np.array([[1,2], [3,4],[5,6]])
    affine1 = np.eye(4)
    f1 = mtf.Fiber(arr2d, affine = affine1)
    f1.xform()
    npt.assert_equal(f1.coords, arr2d)
    f2 = f1.xform(inplace=False)
    npt.assert_equal(f2.coords, f1.coords)
    
    # Keep everything the same, but translate the x coords by 1 downwards
    # http://en.wikipedia.org/wiki/Transformation_matrix#Affine_transformations:
    affine2 = np.matrix([[1, 0, 0, -1],
                         [0, 1, 0,  0],
                         [0, 0, 1,  0],
                         [0, 0, 0,  1]])

    f3 = mtf.Fiber(arr2d, affine=affine2)
    f3.xform()
    npt.assert_equal(f3.coords[0], arr2d[0]-1)

    # This one rotates about the x axis by 90 degrees:
    pi_2 = np.pi/2
    affine3 = np.matrix([[1, 0,             0,            0],
                         [0, np.cos(pi_2), -np.sin(pi_2), 0],
                         [0, np.sin(pi_2),  np.cos(pi_2), 0],
                         [0, 0,             0,            1]])

    f4 = mtf.Fiber([0,1,0], affine=affine3)
    f4.xform()

    # Rotating about the x axis should move all of the length of the vector to
    # the z axis
    npt.assert_almost_equal(f4.coords,[0,0,1])

    # Next time you call xform should bring you back to where you were to begin
    # with 
    f4.xform()
    npt.assert_almost_equal(f4.coords,[0,1,0])

    # If you assign into a new fiber: 
    f5 = f4.xform(inplace=False)
    # This one should have an affine which is the inverse of your original
    # affine:
    npt.assert_equal(f5.affine, affine3.getI())

    # xform-ing twice gives you back the same thing:
    npt.assert_equal(f5.xform(inplace=False).xform(inplace=False).coords,
                     f5.coords)

    npt.assert_equal(f5.xform(inplace=False).xform(inplace=False).affine,
                     f5.affine)

def test_FiberGroup():
    """
    Testing intialization of FiberGroup class.
    """
    
    arr2d = np.array([[1,2], [3,4],[5,6]])
    arr1d = np.array([5,6,7])
    f1 = mtf.Fiber(arr2d, fiber_stats=dict(a=1, b=2))
    f2 = mtf.Fiber(arr1d, fiber_stats=dict(a=1))
    fg1 = mtf.FiberGroup([f1,f2])
    npt.assert_equal(fg1.n_fibers, 2)
    # We have to sort, because it could also come out as ['b', 'a']:
    npt.assert_equal(np.sort(fg1.fiber_stats.keys()), ['a', 'b'])

    # The number of nodes is just the sum of nodes/fiber:
    npt.assert_equal(fg1.n_nodes, f1.n_nodes + f2.n_nodes)

def test_FiberGroup_xform():
    """
    Test affine transformation method of FiberGroup
    """
    
    # This affine rotates vectors 90 degrees around the x axis:
    pi_2 = np.pi/2
    affine1 = np.matrix([[1, 0,             0,            0],
                         [0, np.cos(pi_2), -np.sin(pi_2), 0],
                         [0, np.sin(pi_2),  np.cos(pi_2), 0],
                         [0, 0,             0,            1]])
    

    y = [0,0,1]
    x = [0,1,0]
    f1 = mtf.Fiber(x, affine=affine1)
    f2 = mtf.Fiber(y, affine=affine1)
    fg1 = mtf.FiberGroup([f1,f2])
    fg1.xform()

    # The first fiber's coordinates should be like the second one originally:
    npt.assert_almost_equal(fg1.fibers[0].coords, y)

    f3 = mtf.Fiber(x)
    f4 = mtf.Fiber(y)
    fg2 = mtf.FiberGroup([f3,f4], affine=affine1)

    fg2.xform()
    # Same should be true when the affine is associated with the FiberGroup:
    npt.assert_almost_equal(fg2.fibers[0].coords, y)
    # And the transformtation should have mutated the original object:
    npt.assert_almost_equal(f3.coords, y)

    f5 = mtf.Fiber(x)
    f6 = mtf.Fiber(y)
    fg3 = mtf.FiberGroup([f5,f6])
    fg3.xform(affine1)
    # Same should be true when the affine is provided as input:
    npt.assert_almost_equal(fg3.fibers[0].coords, y)
    # And the transformtation should have mutated the original object:
    npt.assert_almost_equal(f5.coords, y)

    # This also attaches the inverse of this affine to the original object, so
    # that you can always find your way back:
    npt.assert_almost_equal(f5.affine, affine1.getI())

    f7 = mtf.Fiber(x)
    f8 = mtf.Fiber(y)
    fg4 = mtf.FiberGroup([f7,f8])
    fg4.xform()
    npt.assert_equal(fg4.affine, None)

    # The affine should 'stick':
    fg4.xform(np.eye(4))
    npt.assert_equal(fg4.affine, np.eye(4))
    # Even to the fibers:
    npt.assert_equal(f8.affine, np.eye(4))


def test_read_from_pdb():
    """
    Test initialization of the FiberGroup from pdb file

    Benchmark was generated using vistasoft in Matlab as follows:

    >> fg = mtrImportFibers('FG_w_stats.pdb')
    
    """
    data_path = os.path.split(mt.__file__)[0] + '/data/'
    file_name = data_path + "FG_w_stats.pdb"
    fg = mtf.fg_from_pdb(file_name)
    # Get the same fiber group as saved in matlab:
    mat_fg = sio.loadmat(data_path + "fg_from_matlab.mat",
                         squeeze_me=True)["fg"]
    k = [d[0] for d in mat_fg.dtype.descr]
    v = mat_fg.item()
    mat_fg_dict = dict(zip(k,v))
    npt.assert_equal(fg.name, mat_fg_dict["name"])
    npt.assert_equal(fg.fibers[0].coords, mat_fg_dict["fibers"][0])
    npt.assert_equal(fg.fiber_stats["eccentricity"],
                     mat_fg_dict["params"][0].item()[-1])
    
