import pytest
import numpy as np
from scipy.special import erf
from os.path import join, dirname
from numpy.testing import assert_allclose

# Import main modelling routines from empymod directly to ensure they are in
# the __init__.py-file.
from empymod import model
from empymod import bipole, dipole, analytical, loop
# Import rest from model
from empymod.model import gpr, dipole_k, fem, tem
from empymod.kernel import fullspace, halfspace

# These are kind of macro-tests, as they check the final results.
# I try to use different parameters for each test, to cover a wide range of
# possibilities. It won't be possible to check all the possibilities though.
# Add tests when issues arise!

# Load required data
# Data generated with create_self.py
DATAEMPYMOD = np.load(join(dirname(__file__), 'data/empymod.npz'),
                      allow_pickle=True)
# Data generated with create_data/fem_tem.py
DATAFEMTEM = np.load(join(dirname(__file__), 'data/fem_tem.npz'),
                     allow_pickle=True)
# Data generated with create_data/green3d.py
GREEN3D = np.load(join(dirname(__file__), 'data/green3d.npz'),
                  allow_pickle=True)
# Data generated with create_data/dipole1d.py
DIPOLE1D = np.load(join(dirname(__file__), 'data/dipole1d.npz'),
                   allow_pickle=True)
# Data generated with create_data/emmod.py
EMMOD = np.load(join(dirname(__file__), 'data/emmod.npz'),
                allow_pickle=True)
# Data generated with create_data/regression.py
REGRES = np.load(join(dirname(__file__), 'data/regression.npz'),
                 allow_pickle=True)


class TestBipole:
    def test_fullspace(self):
        # Comparison to analytical fullspace solution
        fs = DATAEMPYMOD['fs'][()]
        fsbp = DATAEMPYMOD['fsbp'][()]
        for key in fs:
            # Get fullspace
            fs_res = fullspace(**fs[key])
            # Get bipole
            bip_res = bipole(**fsbp[key])
            # Check
            assert_allclose(fs_res, bip_res)

    def test_halfspace(self):
        # Comparison to analytical halfspace solution
        hs = DATAEMPYMOD['hs'][()]
        hsbp = DATAEMPYMOD['hsbp'][()]
        for key in hs:
            # Get halfspace
            hs_res = halfspace(**hs[key])
            # Get bipole
            bip_res = bipole(**hsbp[key])
            # Check
            if key in ['12', '13', '21', '22', '23', '31']:  # t-domain ex.
                rtol = 1e-2
            else:
                rtol = 1e-7
            assert_allclose(hs_res, bip_res, rtol=rtol)

    def test_emmod(self):
        # Comparison to EMmod (Hunziker et al., 2015)
        # Comparison f = [0.013, 1.25, 130] Hz.; 11 models, 34 ab's, f altern.
        dat = EMMOD['res'][()]
        for _, val in dat.items():
            res = bipole(**val[0])
            assert_allclose(res, val[1], 3e-2, 1e-17, True)

    def test_dipole1d(self):
        # Comparison to DIPOLE1D (Key, Scripps)
        def crec(rec, azm, dip):
            return [rec[0], rec[1], rec[2], azm, dip]

        def get_xyz(src, rec, depth, res, freq, srcpts):
            ex = bipole(src, crec(rec, 0, 0), depth, res, freq, srcpts=srcpts,
                        mrec=False, verb=0)
            ey = bipole(src, crec(rec, 90, 0), depth, res, freq, srcpts=srcpts,
                        mrec=False, verb=0)
            ez = bipole(src, crec(rec, 0, 90), depth, res, freq, srcpts=srcpts,
                        mrec=False, verb=0)
            mx = bipole(src, crec(rec, 0, 0), depth, res, freq, srcpts=srcpts,
                        mrec=True, verb=0)
            my = bipole(src, crec(rec, 90, 0), depth, res, freq, srcpts=srcpts,
                        mrec=True, verb=0)
            mz = bipole(src, crec(rec, 0, 90), depth, res, freq, srcpts=srcpts,
                        mrec=True, verb=0)
            return ex, ey, ez, mx, my, mz

        def comp_all(data, rtol=1e-3, atol=1e-24):
            inp, res = data
            Ex, Ey, Ez, Hx, Hy, Hz = get_xyz(**inp)
            assert_allclose(Ex, res[0], rtol, atol, True)
            assert_allclose(Ey, res[1], rtol, atol, True)
            assert_allclose(Ez, res[2], rtol, atol, True)
            assert_allclose(Hx, res[3], rtol, atol, True)
            assert_allclose(Hy, res[4], rtol, atol, True)
            assert_allclose(Hz, res[5], rtol, atol, True)

        # DIPOLES
        # 1. x-directed dipole
        comp_all(DIPOLE1D['xdirdip'][()])
        # 2. y-directed dipole
        comp_all(DIPOLE1D['ydirdip'][()])
        # 3. z-directed dipole
        comp_all(DIPOLE1D['zdirdip'][()])
        # 4. dipole in xy-plane
        comp_all(DIPOLE1D['xydirdip'][()])
        # 5. dipole in xz-plane
        comp_all(DIPOLE1D['xzdirdip'][()])
        # 6. dipole in yz-plane
        comp_all(DIPOLE1D['yzdirdip'][()])
        # 7. arbitrary xyz-dipole
        comp_all(DIPOLE1D['xyzdirdip'][()])

        # Bipoles
        # 8. x-directed bipole
        comp_all(DIPOLE1D['xdirbip'][()])
        # 9. y-directed bipole
        comp_all(DIPOLE1D['ydirbip'][()])
        # 10. z-directed bipole
        comp_all(DIPOLE1D['zdirbip'][()])
        # 11. bipole in xy-plane
        comp_all(DIPOLE1D['xydirbip'][()])
        # 12. bipole in xz-plane
        comp_all(DIPOLE1D['xzdirbip'][()])
        # 13. bipole in yz-plane
        comp_all(DIPOLE1D['yzdirbip'][()])
        # 14. arbitrary xyz-bipole
        comp_all(DIPOLE1D['xyzdirbip'][()])
        # 14.b Check bipole reciprocity
        inp, res = DIPOLE1D['xyzdirbip'][()]
        ex = bipole(crec(inp['rec'], 0, 0), inp['src'], inp['depth'],
                    inp['res'], inp['freq'], recpts=inp['srcpts'], verb=0)
        assert_allclose(ex, res[0], 2e-2, 1e-24, True)
        mx = bipole(crec(inp['rec'], 0, 0), inp['src'], inp['depth'],
                    inp['res'], inp['freq'], msrc=True, recpts=inp['srcpts'],
                    verb=0)
        assert_allclose(-mx, res[3], 2e-2, 1e-24, True)

    def test_green3d(self):
        # Comparison to green3d (CEMI Consortium)
        def crec(rec, azm, dip):
            return [rec[0], rec[1], rec[2], azm, dip]

        def get_xyz(src, rec, depth, res, freq, aniso, strength, srcpts, msrc):
            ex = bipole(src, crec(rec, 0, 0), depth, res, freq, aniso=aniso,
                        msrc=msrc, mrec=False, strength=strength,
                        srcpts=srcpts, verb=0)
            ey = bipole(src, crec(rec, 90, 0), depth, res, freq, aniso=aniso,
                        msrc=msrc, mrec=False, strength=strength,
                        srcpts=srcpts, verb=0)
            ez = bipole(src, crec(rec, 0, 90), depth, res, freq, aniso=aniso,
                        msrc=msrc, mrec=False, strength=strength,
                        srcpts=srcpts, verb=0)
            mx = bipole(src, crec(rec, 0, 0), depth, res, freq, aniso=aniso,
                        msrc=msrc, mrec=True, strength=strength, srcpts=srcpts,
                        verb=0)
            my = bipole(src, crec(rec, 90, 0), depth, res, freq, aniso=aniso,
                        msrc=msrc, mrec=True, strength=strength, srcpts=srcpts,
                        verb=0)
            mz = bipole(src, crec(rec, 0, 90), depth, res, freq, aniso=aniso,
                        msrc=msrc, mrec=True, strength=strength, srcpts=srcpts,
                        verb=0)
            return ex, ey, ez, mx, my, mz

        def comp_all(data, rtol=1e-3, atol=1e-24):
            inp, res = data
            Ex, Ey, Ez, Hx, Hy, Hz = get_xyz(**inp)
            assert_allclose(Ex, res[0], rtol, atol, True)
            assert_allclose(Ey, res[1], rtol, atol, True)
            assert_allclose(Ez, res[2], rtol, atol, True)
            assert_allclose(Hx, res[3], rtol, atol, True)
            assert_allclose(Hy, res[4], rtol, atol, True)
            assert_allclose(Hz, res[5], rtol, atol, True)

        # ELECTRIC AND MAGNETIC DIPOLES
        # 1. x-directed electric and magnetic dipole
        comp_all(GREEN3D['xdirdip'][()])
        comp_all(GREEN3D['xdirdipm'][()])
        # 2. y-directed electric and magnetic dipole
        comp_all(GREEN3D['ydirdip'][()])
        comp_all(GREEN3D['ydirdipm'][()])
        # 3. z-directed electric and magnetic dipole
        comp_all(GREEN3D['zdirdip'][()], 5e-3)
        comp_all(GREEN3D['zdirdipm'][()], 5e-3)
        # 4. xy-directed electric and magnetic dipole
        comp_all(GREEN3D['xydirdip'][()])
        comp_all(GREEN3D['xydirdipm'][()])
        # 5. xz-directed electric and magnetic dipole
        comp_all(GREEN3D['xzdirdip'][()], 5e-3)
        comp_all(GREEN3D['xzdirdipm'][()], 5e-3)
        # 6. yz-directed electric and magnetic dipole
        comp_all(GREEN3D['yzdirdip'][()], 5e-3)
        comp_all(GREEN3D['yzdirdipm'][()], 5e-3)
        # 7. xyz-directed electric and magnetic dipole
        comp_all(GREEN3D['xyzdirdip'][()], 2e-2)
        comp_all(GREEN3D['xyzdirdipm'][()], 2e-2)
        # 7.b Check magnetic dipole reciprocity
        inp, res = GREEN3D['xyzdirdipm'][()]
        ey = bipole(crec(inp['rec'], 90, 0), inp['src'], inp['depth'],
                    inp['res'], inp['freq'], None, inp['aniso'],
                    mrec=inp['msrc'], msrc=False, strength=inp['strength'],
                    srcpts=1, recpts=inp['srcpts'], verb=0)
        assert_allclose(-ey, res[1], 2e-2, 1e-24, True)

        # ELECTRIC AND MAGNETIC BIPOLES
        # 8. x-directed electric and magnetic bipole
        comp_all(GREEN3D['xdirbip'][()], 5e-3)
        comp_all(GREEN3D['xdirbipm'][()], 5e-3)
        # 8.b Check electric bipole reciprocity
        inp, res = GREEN3D['xdirbip'][()]
        ex = bipole(crec(inp['rec'], 0, 0), inp['src'], inp['depth'],
                    inp['res'], inp['freq'], None, inp['aniso'],
                    mrec=inp['msrc'], msrc=False, strength=inp['strength'],
                    srcpts=1, recpts=inp['srcpts'], verb=0)
        assert_allclose(ex, res[0], 5e-3, 1e-24, True)
        # 9. y-directed electric and magnetic bipole
        comp_all(GREEN3D['ydirbip'][()], 5e-3)
        comp_all(GREEN3D['ydirbipm'][()], 5e-3)
        # 10. z-directed electric and magnetic bipole
        comp_all(GREEN3D['zdirbip'][()], 5e-3)
        comp_all(GREEN3D['zdirbipm'][()], 5e-3)

    def test_status_quo(self):
        # Comparison to self, to ensure nothing changed.
        # 4 bipole-bipole cases in EE, ME, EM, MM, all different values
        for i in ['1', '2', '3', '4']:
            res = DATAEMPYMOD['out'+i][()]
            tEM = bipole(**res['inp'])
            assert_allclose(tEM, res['EM'], rtol=5e-5)  # 5e-5 shouldn't be...

    def test_dipole_bipole(self):
        # Compare a dipole to a bipole
        # Checking intpts, strength, reciprocity
        inp = {'depth': [0, 250], 'res': [1e20, 0.3, 5], 'freqtime': 1}
        rec = [8000, 200, 300, 0, 0]
        bip1 = bipole([-25, 25, -25, 25, 100, 170.7107], rec, srcpts=1,
                      strength=33, **inp)
        bip2 = bipole(rec, [-25, 25, -25, 25, 100, 170.7107], recpts=5,
                      strength=33, **inp)
        dip = bipole([0, 0, 135.3553, 45, 45], [8000, 200, 300, 0, 0], **inp)
        # r = 100; sI = 33 => 3300
        assert_allclose(bip1, dip*3300, 1e-5)  # bipole as dipole
        assert_allclose(bip2, dip*3300, 1e-2)  # bipole, src/rec switched.

    def test_loop(self, capsys):
        # Compare loop options: None, 'off', 'freq'
        inp = {'depth': [0, 500], 'res': [10, 3, 50], 'freqtime': [1, 2, 3],
               'rec': [[6000, 7000, 8000], [200, 200, 200], 300, 0, 0],
               'src': [0, 0, 0, 0, 0]}

        non = bipole(loop=None, verb=3, **inp)
        out, _ = capsys.readouterr()
        assert "Loop over       :  None (all vectorized)" in out

        lpo = bipole(loop='off', verb=3, **inp)
        out, _ = capsys.readouterr()
        assert "Loop over       :  Offsets" in out
        assert_allclose(non, lpo, equal_nan=True)

        lfr = bipole(loop='freq', verb=3, **inp)
        out, _ = capsys.readouterr()
        assert "Loop over       :  Frequencies" in out
        assert_allclose(non, lfr, equal_nan=True)

    def test_hankel(self, capsys):
        # Compare Hankel transforms
        inp = {'depth': [-20, 100], 'res': [1e20, 5, 100],
               'freqtime': [1.34, 23, 31], 'src': [0, 0, 0, 0, 90],
               'rec': [[200, 300, 400], [3000, 4000, 5000], 120, 90, 0]}

        dlf = bipole(ht='dlf', htarg={'pts_per_dec': 0}, verb=3, **inp)
        out, _ = capsys.readouterr()
        assert "Hankel          :  DLF (Fast Hankel Transform)" in out
        assert "  > DLF type    :  Standard" in out
        assert "Loop over       :  None" in out

        dlf2 = bipole(ht='dlf', htarg={'pts_per_dec': -1}, verb=3, **inp)
        out, _ = capsys.readouterr()
        assert "Hankel          :  DLF (Fast Hankel Transform)" in out
        assert "  > DLF type    :  Lagged Convolution" in out
        assert "Loop over       :  Frequencies" in out
        assert_allclose(dlf, dlf2, rtol=1e-4)

        dlf3 = bipole(ht='dlf', htarg={'pts_per_dec': 40}, verb=3, **inp)
        out, _ = capsys.readouterr()
        assert "Hankel          :  DLF (Fast Hankel Transform)" in out
        assert "  > DLF type    :  Splined, 40.0 pts/dec" in out
        assert "Loop over       :  Frequencies" in out
        assert_allclose(dlf, dlf3, rtol=1e-3)

        qwe = bipole(ht='qwe', htarg={'pts_per_dec': 0}, verb=3, **inp)
        out, _ = capsys.readouterr()
        assert "Hankel          :  Quadrature-with-Extrapolation" in out
        assert_allclose(dlf, qwe, equal_nan=True)

        quad = bipole(ht='quad', htarg={'b': 1, 'pts_per_dec': 1000}, verb=3,
                      **inp)
        out, _ = capsys.readouterr()
        assert "Hankel          :  Quadrature" in out
        assert_allclose(dlf, quad, equal_nan=True)

    def test_fourier(self, capsys):
        # Compare Fourier transforms
        inp = {'depth': [0, 300], 'res': [1e12, 1/3, 5],
               'freqtime': np.logspace(-1.5, 1, 20), 'signal': 0,
               'rec': [2000, 300, 280, 0, 0], 'src': [0, 0, 250, 0, 0]}

        ftl = bipole(ft='fftlog', verb=3, **inp)
        out, _ = capsys.readouterr()
        assert "Fourier         :  FFTLog" in out

        qwe = bipole(ft='qwe', ftarg={'pts_per_dec': 30}, verb=3, **inp)
        out, _ = capsys.readouterr()
        assert "Fourier         :  Quadrature-with-Extrapolation" in out
        assert_allclose(qwe, ftl, 1e-2, equal_nan=True)

        dlf = bipole(ft='dlf', verb=3, **inp)
        out, _ = capsys.readouterr()
        assert "Fourier         :  DLF (Sine-Filter)" in out
        assert_allclose(dlf, ftl, 1e-2, equal_nan=True)

        # FFT: We keep the error-check very low, otherwise we would have to
        #      calculate too many frequencies.
        fft = bipole(
                ft='fft',
                ftarg={'dfreq': 0.002, 'nfreq': 2**13, 'ntot': 2**16},
                verb=3, **inp)
        out, _ = capsys.readouterr()
        assert "Fourier         :  Fast Fourier Transform FFT" in out
        assert_allclose(fft, ftl, 1e-1, 1e-13, equal_nan=True)

    def test_example_wrong(self):
        # One example of wrong input. But inputs are checked in test_utils.py.
        with pytest.raises(ValueError, match="Parameter src has wrong length"):
            bipole([0, 0, 0], [0, 0, 0, 0, 0], [], 1, 1, verb=0)

    def test_combinations(self):
        # These are the 15 options that each bipole (src or rec) can take.
        # There are therefore 15x15 possibilities for src-rec combination
        # within bipole!
        # Here we are just checking a few possibilities... But these should
        # cover the principle and therefore hold for all cases.
        inp = {'depth': [-100, 300], 'res': [1e20, 1, 10],
               'freqtime': [0.5, 0.9], 'src': [0, 0, 0, 0, 0]}

        #                one_depth  dipole  asdipole one_bpdepth
        #   =====================================================
        #    .   .   .       TRUE     TRUE     TRUE     TRUE
        #   -----------------------------------------------------
        #    |   |   .       TRUE     TRUE     TRUE     TRUE
        #   -----------------------------------------------------
        #    |   |   |      false     TRUE     TRUE     TRUE
        #   -----------------------------------------------------
        #   . . . . . .      TRUE    false     TRUE     TRUE
        #                    TRUE    false    false     TRUE
        #                    TRUE    false     TRUE    false
        #                    TRUE    false    false    false
        #   -----------------------------------------------------
        #   | | | | . .      TRUE    false     TRUE     TRUE
        #                    TRUE    false    false     TRUE
        #                    TRUE    false     TRUE    false
        #                    TRUE    false    false    false
        #   -----------------------------------------------------
        #   | | | | | |     false    false     TRUE     TRUE
        #                   false    false    false     TRUE
        #                   false    false     TRUE    false
        #                   false    false    false    false
        #   -----------------------------------------------------

        # 1.1 three different dipoles
        da = bipole(rec=[7000, 500, 100, 0, 0], **inp)
        db = bipole(rec=[8000, 500, 200, 0, 0], **inp)
        dc = bipole(rec=[9000, 500, 300, 0, 0], **inp)

        # 1.2 three dipoles at same depth at once => comp to 1.1
        dd = bipole(rec=[[7000, 8000, 9000], [500, 500, 500], 100, 0, 0],
                    **inp)
        de = bipole(rec=[[7000, 8000, 9000], [500, 500, 500], 200, 0, 0],
                    **inp)
        df = bipole(rec=[[7000, 8000, 9000], [500, 500, 500], 300, 0, 0],
                    **inp)
        assert_allclose(dd[:, 0], da)
        assert_allclose(de[:, 1], db)
        assert_allclose(df[:, 2], dc)

        # 1.3 three dipoles at different depths at once => comp to 1.1
        dg = bipole(rec=[[7000, 8000, 9000], [500, 500, 500], [100, 200, 300],
                    0, 0], **inp)
        assert_allclose(dg[:, 0], da)
        assert_allclose(dg[:, 1], db)
        assert_allclose(dg[:, 2], dc)

        # 2.1 three different bipoles
        # => asdipole/!asdipole/one_bpdepth/!one_bpdepth
        ba = bipole(rec=[7000, 7050, 100, 100, 2.5, 2.5], **inp)
        bb = bipole(rec=[7000, 7050, 100, 100, 2.5, 2.5], recpts=10, **inp)
        bc = bipole(rec=[7000, 7050, 100, 100, 0, 5], **inp)
        bd = bipole(rec=[7000, 7050, 100, 100, 0, 5], recpts=10, **inp)
        assert_allclose(ba, bb, 1e-3)
        assert_allclose(bc, bd, 1e-3)
        assert_allclose(ba, bc, 1e-2)  # As the dip is very small

        # 2.2 three bipoles at same depth at once
        # => asdipole/!asdipole/one_bpdepth/!one_bpdepth => comp to 2.1
        be = bipole(rec=[[7000, 8000, 9000], [7050, 8050, 9050],
                         [100, 100, 100], [100, 100, 100], 2.5, 2.5], **inp)
        bf = bipole(rec=[[7000, 8000, 9000], [7050, 8050, 9050],
                         [100, 100, 100], [100, 100, 100], 2.5, 2.5],
                    recpts=10, **inp)
        bg = bipole(rec=[[7000, 8000, 9000], [7050, 8050, 9050],
                    [100, 100, 100], [100, 100, 100], 0, 5], **inp)
        bh = bipole(rec=[[7000, 8000, 9000], [7050, 8050, 9050],
                         [100, 100, 100], [100, 100, 100], 0, 5], recpts=10,
                    **inp)
        assert_allclose(be[:, 0], ba)
        assert_allclose(bf[:, 0], bb)
        assert_allclose(bg[:, 0], bc)
        assert_allclose(bh[:, 0], bd)
        assert_allclose(be, bf, 1e-3)
        assert_allclose(bg, bh, 1e-3)
        assert_allclose(be, bg, 1e-2)  # As the dip is very small

    def test_combinations2(self):
        # Additional to test_combinations: different src- and rec-
        # bipoles at the same time
        inp = {'depth': [0.75, 500], 'res': [20, 5, 11],
               'freqtime': [1.05, 3.76], 'verb': 0}

        # Source bipoles and equivalent dipoles
        srcbip = [[-1, -1], [1, 1], [0, -1], [0, 1], [100, 200], [100, 200]]
        srcdip1 = [0, 0, 100, 0, 0]
        srcdip2 = [0, 0, 200, 45, 0]

        # Receiver bipoles and equivalent dipoles
        recbip = [[7999, 7999], [8001, 8001], [0, 0], [0, 0],
                  [200, 300], [200, 300]]
        recdip1 = [8000, 0, 200, 0, 0]
        recdip2 = [8000, 0, 300, 0, 0]

        # 1. calculate all bipoles at once
        bip = bipole(srcbip, recbip, **inp)

        # 2. calculate each dipole separate
        dip1 = bipole(srcdip1, recdip1, **inp)
        dip2 = bipole(srcdip1, recdip2, **inp)
        dip3 = bipole(srcdip2, recdip1, **inp)
        dip4 = bipole(srcdip2, recdip2, **inp)

        # 3. compare
        assert_allclose(bip[:, 0, 0], dip1)
        assert_allclose(bip[:, 1, 0], dip2)
        assert_allclose(bip[:, 0, 1], dip3)
        assert_allclose(bip[:, 1, 1], dip4)

    def test_multisrc_multirec(self):
        # Check that a multi-source, multi-receiver results in the same as if
        # calculated on their own.

        # General model parameters
        model = {
            'depth': [0, 1000],
            'res': [2e14, 0.3, 1],
            'freqtime': 1,
            'verb': 0}

        # Multi-src (0) and single sources (1), (2)
        src0 = [[0, 100], [50, 200], [0, 10], [200, -30],
                [950, 930], [955, 900]]
        src1 = [0, 50, 0, 200, 950, 955]
        src2 = [100, 200, 10, -30, 930, 900]

        # Multi-rec (0) and single receivers (1), (2)
        rec0 = [[4000, 5000], [4100, 5200], [0, 100], [100, 250],
                [950, 990], [990, 1000]]
        rec1 = [4000, 4100, 0, 100, 950, 990]
        rec2 = [5000, 5200, 100, 250, 990, 1000]

        # Calculate the multi-src/multi-rec result
        out0f = bipole(src=src0, rec=rec0, signal=None, **model)
        out0t = bipole(src=src0, rec=rec0, signal=0, **model)

        # Calculate the single-src/single-rec correspondents
        out1f = np.zeros((2, 2), dtype=np.complex128)
        out1t = np.zeros((2, 2))
        for i, rec in enumerate([rec1, rec2]):
            for ii, src in enumerate([src1, src2]):
                out1f[i, ii] = bipole(src=src, rec=rec, signal=None, **model)
                out1t[i, ii] = bipole(src=src, rec=rec, signal=0, **model)

        # Check them
        assert_allclose(out0f, out1f)
        assert_allclose(out0t, out1t)

    def test_cole_cole(self):
        # Check user-hook for eta/zeta

        def func_eta(inp, pdict):
            # Dummy function to check if it works.
            etaH = pdict['etaH'].real*inp['fact'] + 1j*pdict['etaH'].imag
            etaV = pdict['etaV'].real*inp['fact'] + 1j*pdict['etaV'].imag

            return etaH, etaV

        def func_zeta(inp, pdict):
            # Dummy function to check if it works.
            etaH = pdict['zetaH']/inp['fact']
            etaV = pdict['zetaV']/inp['fact']

            return etaH, etaV

        model = {'src': [0, 0, 500, 0, 0], 'rec': [500, 0, 600, 0, 0],
                 'depth': [0, 550], 'freqtime': [0.1, 1, 10]}
        res = np.array([2, 10, 5])
        fact = np.array([2, 2, 2])
        eta = {'res': fact*res, 'fact': fact, 'func_eta': func_eta}
        zeta = {'res': res, 'fact': fact, 'func_zeta': func_zeta}

        # Frequency domain
        standard = bipole(res=res, **model)
        outeta = bipole(res=eta, **model)
        assert_allclose(standard, outeta)
        outzeta = bipole(res=zeta, mpermH=fact, mpermV=fact, **model)
        assert_allclose(standard, outzeta)
        # Time domain
        standard = bipole(res=res, signal=0, **model)
        outeta = bipole(res=eta, signal=0, **model)
        assert_allclose(standard, outeta)
        outzeta = bipole(res=zeta, signal=0, mpermH=fact, mpermV=fact, **model)
        assert_allclose(standard, outzeta)

    def test_src_rec_definitions(self):
        inp = {'depth': [0, -250], 'res': [1e20, 0.3, 5], 'freqtime': 1.23456}

        src1 = [[0, 0], [20, 0], [0, 0], [0, 20], -200, -200]
        src2 = [[10, 0], [0, 10], -200, [0, 90], [0, 0]]

        rec1 = [[1000, 0, 1000], [1200, 0, 1200],
                [0, 1000, 1000], [0, 1200, 1200],
                -250, -250]
        rec2 = [[1100, 0, 1100], [0, 1100, 1100], -250, [0, 90, 45], [0, 0, 0]]

        bip1 = bipole(src1, rec1, **inp)  # [x1, x2, y1, y2, z1, z2]
        bip2 = bipole(src2, rec2, **inp)  # [x, y, z, azimuth, dip]

        assert_allclose(bip1[:, :], bip2[:, :])

    def test_shape(self):

        inp = {'depth': [], 'res': 1.0, 'freqtime': (1.0, 2.0), 'verb': 1}

        a = bipole(src=[0, 10, 1, 0, 90], rec=[10, 10, 10, 11, 1], **inp)
        b = bipole(src=[-50, 0, 1, 10, 90], rec=[10, 10, 10, 11, 1], **inp)
        c = bipole(src=[0, 10, 1, 0, 90], rec=[20, 10, 10, 11, 0], **inp)
        d = bipole(src=[-50, 0, 1, 10, 90], rec=[20, 10, 10, 11, 0], **inp)

        # Several sources, several receivers
        out = bipole(src=[[0, -50], [10, 0], 1, [0, 10], 90],
                     rec=[[10, 20], [10, 10], 10, 11, [1, 0]], **inp)
        assert_allclose(out[:, 0, 0], a)
        assert_allclose(out[:, 0, 1], b)
        assert_allclose(out[:, 1, 0], c)
        assert_allclose(out[:, 1, 1], d)

        # One source, one receiver
        out = bipole(src=[-50, 0, 1, 10, 90],
                     rec=[10, 10, 10, 11, 1], **inp)
        assert_allclose(out, b)

        # Several sources, one receiver
        out = bipole(src=[[0, -50], [10, 0], 1, [0, 10], 90],
                     rec=[10, 10, 10, 11, 1], **inp)
        assert_allclose(out[:, 0], a)
        assert_allclose(out[:, 1], b)

        # One sources, several receivers
        out = bipole(src=[-50, 0, 1, 10, 90],
                     rec=[[10, 20], [10, 10], 10, 11, [1, 0]], **inp)
        assert_allclose(out[:, 0], b)
        assert_allclose(out[:, 1], d)

    def test_j(self, capsys):
        # Compare a electric * sigma with j
        inp = {
            'src': [-25, 25, -25, 25, 100, 170.7107],
            'rec': [8000, 200, 300, 0, 0],
            'depth': [0, 250],
            'res': [1e20, 0.3, 5],
            'freqtime': 1,
        }
        efield = bipole(**inp)
        ecurr = bipole(mrec='j', **inp)
        assert_allclose(efield/5, ecurr)

        # Check warning
        inp['aniso'] = [1, 1, 2]
        efield = bipole(**inp)
        _, _ = capsys.readouterr()  # Empty it
        ecurr = bipole(mrec='j', **inp)
        out, _ = capsys.readouterr()
        assert_allclose(efield/5, ecurr)
        assert "* WARNING :: `etaH != etaV` at receiver level, " in out


def test_dipole():
    # As this is a subset of bipole, just run two tests to ensure
    # it is equivalent to bipole.

    # 1. Frequency
    src = [5000, 1000, -200]
    rec = [0, 0, 1200]
    model = {'depth': [100, 1000], 'res': [2, 0.3, 100], 'aniso': [2, .5, 2]}
    f = 0.01
    # v  dipole : ab = 26
    # \> bipole : src-dip = 90, rec-azimuth=90, msrc=True
    dip_res = dipole(src, rec, freqtime=f, ab=26, verb=0, **model)
    bip_res = bipole([src[0], src[1], src[2], 0, 90],
                     [rec[0], rec[1], rec[2], 90, 0], msrc=True, freqtime=f,
                     verb=0, **model)
    assert_allclose(dip_res, bip_res)

    # 1b. Check RHS and LHS
    imodel = {'depth': [-1000, -100], 'res': [100, 0.3, 2],
              'aniso': [2, .5, 2]}
    idip_res = dipole([src[0], src[1], -src[2]], [rec[0], rec[1], -rec[2]],
                      freqtime=f, ab=26, verb=0, **imodel)
    ibip_res = bipole([src[0], src[1], -src[2], 0, 90],
                      [rec[0], rec[1], -rec[2], 90, 0], msrc=True, freqtime=f,
                      verb=0, **imodel)
    assert_allclose(idip_res, dip_res)
    assert_allclose(ibip_res, bip_res)

    # 2. Time
    t = 1
    dip_res = dipole(src, rec, freqtime=t, signal=1, ab=62, verb=0, **model)
    bip_res = bipole([src[0], src[1], src[2], 0, 90],
                     [rec[0], rec[1], rec[2], 90, 0], msrc=True, freqtime=t,
                     signal=1, verb=0, **model)
    assert_allclose(dip_res, bip_res)

    # 3. Check user-hook for eta/zeta
    def func_eta(inp, pdict):
        # Dummy function to check if it works.
        etaH = pdict['etaH'].real*inp['fact'] + 1j*pdict['etaH'].imag
        etaV = pdict['etaV'].real*inp['fact'] + 1j*pdict['etaV'].imag

        return etaH, etaV

    def func_zeta(inp, pdict):
        # Dummy function to check if it works.
        etaH = pdict['zetaH']/inp['fact']
        etaV = pdict['zetaV']/inp['fact']

        return etaH, etaV

    model = {'src': [0, 0, 500], 'rec': [500, 0, 600], 'depth': [0, 550],
             'freqtime': [0.1, 1, 10]}
    res = np.array([2, 10, 5])
    fact = np.array([2, 2, 2])
    eta = {'res': fact*res, 'fact': fact, 'func_eta': func_eta}
    zeta = {'res': res, 'fact': fact, 'func_zeta': func_zeta}

    # Frequency domain
    standard = dipole(res=res, **model)
    outeta = dipole(res=eta, **model)
    assert_allclose(standard, outeta)
    outzeta = dipole(res=zeta, mpermH=fact, mpermV=fact, **model)
    assert_allclose(standard, outzeta)
    # Time domain
    standard = dipole(res=res, signal=0, **model)
    outeta = dipole(res=eta, signal=0, **model)
    assert_allclose(standard, outeta)
    outzeta = dipole(res=zeta, signal=0, mpermH=fact, mpermV=fact, **model)
    assert_allclose(standard, outzeta)


def test_all_depths():
    # Test RHS/LHS low-to-high/high-to-low
    src = [0, 0, 10]
    rec = [500, 100, 50]
    freq = 1
    depth = np.array([-50, 0, 100, 2000])
    res = [6, 1, 2, 3, 4]
    aniso = [6, 7, 8, 9, 10]
    epermH = [1.0, 1.1, 1.2, 1.3, 1.4]
    epermV = [1.5, 1.6, 1.7, 1.8, 1.9]
    mpermH = [2.0, 2.1, 2.2, 2.3, 2.4]
    mpermV = [2.5, 2.6, 2.7, 2.8, 2.9]

    # 1. Ordering as internally used:
    inp = {'ab': 11, 'aniso': aniso, 'epermH': epermH, 'epermV': epermV,
           'mpermH': mpermH, 'mpermV': mpermV}

    # LHS low-to-high (+1, ::+1)
    lhs_l2h = dipole(src, rec, depth, res, freq, **inp)

    # RHS high-to-low (-1, ::+1)
    rhs_h2l = dipole([src[0], src[1], -src[2]], [rec[0], rec[1], -rec[2]],
                     -depth, res, freq, **inp)

    # 2. Reversed ordering:
    inp_r = {'ab': 11, 'aniso': aniso[::-1], 'epermH': epermH[::-1], 'epermV':
             epermV[::-1], 'mpermH': mpermH[::-1], 'mpermV': mpermV[::-1]}

    # LHS high-to-low (+1, ::-1)
    lhs_h2l = dipole(src, rec, depth[::-1], res[::-1], freq, **inp_r)

    # RHS low-to-high (-1, ::-1)
    rhs_l2h = dipole([src[0], src[1], -src[2]], [rec[0], rec[1], -rec[2]],
                     -depth[::-1], res[::-1], freq, **inp_r)

    assert_allclose(lhs_l2h, lhs_h2l)
    assert_allclose(lhs_l2h, rhs_l2h)
    assert_allclose(lhs_l2h, rhs_h2l)


def test_coordinate_systems():
    srcLHS = (0, 0, -10)
    srcRHS = (0, 0, +10)

    x = np.arange(1, 11)*1000
    recLHS = (x, x, +3)
    recRHS = (x, x, -3)

    air, hs, tg = 2e14, 100, 1000
    z0, z1, z2 = 0, 10, 20

    inp = {'freqtime': 1, 'verb': 1}
    inpLHS = {'src': srcLHS, 'rec': recLHS}
    inpRHS = {'src': srcRHS, 'rec': recRHS}

    for ab in [11, 31, 23, 33, 25, 35, 16, 66, 51, 61, 43, 63, 44, 65, 56, 66]:
        # Sign switches occur for each z-component; each m-component
        sign = 1
        if ab % 10 > 3:   # If True: magnetic src
            sign *= -1
        if ab // 10 > 3:  # If True: magnetic rec
            sign *= -1
        if str(ab)[0] in ['3', '6']:  # Vertical source component
            sign *= -1
        if str(ab)[1] in ['3', '6']:  # Vertical receiver component
            sign *= -1
        inp['ab'] = ab

        # # 2-layer case

        # Default/original: LHS low to high
        orig = dipole(depth=z0, res=[air, hs], **inpLHS, **inp)

        # Alternatives LHS: low to high and high to low
        LHSl2h = dipole(depth=[z0, np.inf], res=[air, hs], **inpLHS, **inp)
        LHSh2l = dipole(depth=[np.inf, z0], res=[hs, air], **inpLHS, **inp)

        assert_allclose(orig, LHSl2h)
        assert_allclose(orig, LHSh2l)

        # Alternatives LHS: low to high and high to low
        RHSlth = sign*dipole(
            depth=[-np.inf, -z0], res=[hs, air], **inpRHS, **inp)
        RHSh2l = sign*dipole(
            depth=[-z0, -np.inf], res=[air, hs], **inpRHS, **inp)

        assert_allclose(orig, RHSlth, rtol=5e-6)
        assert_allclose(orig, RHSh2l, rtol=5e-6)

        # # 4-layer case

        # Default/original: LHS low to high
        orig = dipole(
            depth=[z0, z1, z2], res=[air, hs, tg, hs], **inpLHS, **inp)

        # Alternatives LHS: low to high and high to low
        LHSh2l = dipole(
            depth=[z2, z1, z0], res=[hs, tg, hs, air], **inpLHS, **inp)

        assert_allclose(orig, LHSh2l)

        # Alternatives LHS: low to high and high to low
        RHSlth = sign*dipole(
            depth=[-z2, -z1, -z0], res=[hs, tg, hs, air], **inpRHS, **inp)
        RHSh2l = sign*dipole(
            depth=[-z0, -z1, -z2], res=[air, hs, tg, hs], **inpRHS, **inp)

        assert_allclose(orig, RHSlth)
        assert_allclose(orig, RHSh2l)


class TestLoop:
    # Loop is a subset of bipole, with a frequency-dependent factor at the
    # frequency level.

    def test_bipole(self, capsys):
        # 1. Compare to bipole in the frequency domain, to ensure it is the
        # same.

        # Survey parameters.
        depth = [0, 200]
        res = [2e14, 100, 200]
        freq = np.logspace(-4, 4, 101)

        # 1.a: msrc-mrec; nrec==nrecz, nsrc!=nsrcz.
        rec = [100, 0, 0, 23, -50]
        src = [[0, 0, 0], [0, 0, 0], 0, 45, 33]
        loo = loop(src, rec, depth, res, freq)
        bip = bipole(src, rec, depth, res, freq, msrc=True, mrec=True)
        bip *= 2j*np.pi*freq[:, None]*4e-7*np.pi
        assert_allclose(bip, loo, rtol=1e-4, atol=1e-18)

        # 1.b: msrc-erec; nrec!=nrecz, nsrc!=nsrcz.
        rec = [[100, 200, 300], [-10, 0, 10], 0, 23, -50]
        src = [[0, 0, 0], [0, 0, 0], 0, 45, 33]
        loo = loop(src, rec, depth, res, freq, mrec=False, strength=np.pi)
        bip = bipole(src, rec, depth, res, freq, msrc=True, mrec=False,
                     strength=np.pi)*2j*np.pi*freq[:, None, None]*4e-7*np.pi
        assert_allclose(bip, loo, rtol=1e-4, atol=1e-18)

        # 1.c: msrc-looprec; nrec==nrecz, nsrc!=nsrcz.
        rec = [[100, 100, 100], [0, 0, 0], [-10, 0, 10], 23, -50]
        src = [[0, 0, 0], [0, 0, 0], 0, 45, 33]
        loo = loop(src, rec, depth, res, freq, mrec='loop')
        bip = bipole(src, rec, depth, res, freq, msrc=True, mrec=True)
        bip *= (2j*np.pi*freq[:, None, None]*4e-7*np.pi)**2
        assert_allclose(bip, loo, rtol=1e-4, atol=1e-18)

        # 1.d: msrc-loopre; nrec!=nrecz, nsrc==nsrcz.
        _, _ = capsys.readouterr()  # Empty it
        rec = [[100, 100, 100], [0, 0, 0], 0, 23, -50]
        src = [[0, 0, 0], [0, 0, 0], [-10, 0, 10], 45, 33]
        mpermH = [1, 1, 1]
        mpermV = [1.5, 2, 1]
        loo = loop(src, rec, depth, res, freq, mrec='loop', mpermH=mpermH,
                   mpermV=mpermV)
        out, _ = capsys.readouterr()
        bip = bipole(src, rec, depth, res, freq, msrc=True, mrec=True,
                     mpermH=mpermH, mpermV=mpermV)
        bip *= (2j*np.pi*freq[:, None, None]*4e-7*np.pi)**2
        assert_allclose(bip, loo, rtol=1e-4, atol=1e-18)
        assert '* WARNING :: `mpermH != mpermV` at source level, ' in out
        assert '* WARNING :: `mpermH != mpermV` at receiver level, ' in out

    def test_iso_fs(self):
        # 2. Test with isotropic full-space solution, Ward and Hohmann, 1988.
        # => em with ab=24; Eq. 2.58, Ward and Hohmann, 1988.

        # Survey parameters.
        src = [0, 0, 0, 0, 0]
        rec = [100, 0, 100, -90, 0]
        res = 100
        time = np.logspace(-4, 0, 301)

        # Calculation.
        fhz_num2 = loop(src, rec, [], res, time, mrec=False, xdirect=True,
                        verb=1, signal=1)

        # Analytical solution.
        mu_0 = 4e-7*np.pi
        r = np.sqrt(rec[0]**2+rec[1]**2+rec[2]**2)
        theta = np.sqrt(mu_0/(4*res*time))
        theta_r = theta*r
        ana_sol2 = - mu_0*theta**3*rec[2]*np.exp(-theta_r**2)
        ana_sol2 /= 2*np.pi**1.5*time

        # Check.
        assert_allclose(fhz_num2, ana_sol2, rtol=1e-4, atol=1e-18)

    def test_iso_hs(self):
        # 3. Test with isotropic half-space solution, Ward and Hohmann, 1988.
        # => mm with ab=66; Eq. 4.70, Ward and Hohmann, 1988.

        # Survey parameters.
        # time: cut out zero crossing.
        mu_0 = 4e-7*np.pi
        time = np.r_[np.logspace(-7.3, -5.7, 101), np.logspace(-4.3, 0, 101)]
        src = [0, 0, 0, 0, 90]
        rec = [100, 0, 0, 0, 90]
        res = 100.

        # Calculation.
        fhz_num1 = loop(src, rec, 0, [2e14, res], time, xdirect=True, verb=1,
                        epermH=[0, 1], epermV=[0, 1], signal=0)

        # Analytical solution.
        theta = np.sqrt(mu_0/(4*res*time))
        theta_r = theta*rec[0]
        ana_sol1 = (9 + 6 * theta_r**2 + 4 * theta_r**4) * np.exp(-theta_r**2)
        ana_sol1 *= -2 * theta_r / np.sqrt(np.pi)
        ana_sol1 += 9 * erf(theta_r)
        ana_sol1 *= -res/(2*np.pi*mu_0*rec[0]**5)

        # Check.
        assert_allclose(fhz_num1, ana_sol1, rtol=1e-4)

    def test_cole_cole(self):
        # Just compare to bipole.

        def func_eta(inp, pdict):
            # Dummy function to check if it works.
            etaH = pdict['etaH'].real*inp['fact'] + 1j*pdict['etaH'].imag
            etaV = pdict['etaV'].real*inp['fact'] + 1j*pdict['etaV'].imag

            return etaH, etaV

        def func_zeta(inp, pdict):
            # Dummy function to check if it works.
            etaH = pdict['zetaH']/inp['fact']
            etaV = pdict['zetaV']/inp['fact']

            return etaH, etaV

        freq = 1.
        model = {'src': [0, 0, 500, 0, 0], 'rec': [500, 0, 600, 0, 0],
                 'depth': [0, 550], 'freqtime': freq}
        res = np.array([2, 10, 5])
        fact = np.array([2, 2, 2])
        eta = {'res': fact*res, 'fact': fact, 'func_eta': func_eta}
        zeta = {'res': res, 'fact': fact, 'func_zeta': func_zeta}

        # Frequency domain
        etabip = bipole(res=eta, msrc=True, mrec=True, **model)
        etabip *= 2j*np.pi*freq*4e-7*np.pi
        etaloo = loop(res=eta, **model)
        assert_allclose(etabip, etaloo)

        zetabip = bipole(res=zeta, mpermH=fact, mpermV=fact, msrc=True,
                         mrec=True, **model)
        zetabip *= 2j*np.pi*freq*4e-7*np.pi
        zetaloo = loop(res=zeta, mpermH=fact, mpermV=fact, **model)
        assert_allclose(zetabip, zetaloo)


def test_analytical():
    # 1. fullspace
    model = {'src': [500, -100, -200],
             'rec': [0, 1000, 200],
             'res': 6.71,
             'aniso': 1.2,
             'freqtime': 40,
             'ab': 42,
             'verb': 0}
    dip_res = dipole(depth=[], **model)
    ana_res = analytical(**model)
    assert_allclose(dip_res, ana_res)
    # \= Check 36/63
    model['ab'] = 63
    ana_res2 = analytical(**model)
    assert_allclose(ana_res.shape, ana_res.shape)
    assert np.count_nonzero(ana_res2) == 0

    # 2. halfspace
    for signal in [None, 0, 1]:  # Frequency, Time
        model = {'src': [500, -100, 5],
                 'rec': [0, 1000, 20],
                 'res': 6.71,
                 'aniso': 1.2,
                 'freqtime': 1,
                 'signal': signal,
                 'ab': 12,
                 'verb': 0}
        # Check dhs, dsplit, and dtetm
        ana_res = analytical(solution='dhs', **model)
        res1, res2, res3 = analytical(solution='dsplit', **model)
        dTE, dTM, rTE, rTM, air = analytical(solution='dtetm', **model)
        model['res'] = [2e14, model['res']]
        model['aniso'] = [1, model['aniso']]
        dip_res = dipole(depth=0, **model)
        # Check dhs, dsplit
        assert_allclose(dip_res, ana_res, rtol=1e-3)
        assert_allclose(ana_res, res1+res2+res3)
        # Check dsplit and dtetm
        assert_allclose(res1, dTE+dTM)
        assert_allclose(res2, rTE+rTM)
        assert_allclose(res3, air)

    # As above, but Laplace domain.
    model = {'src': [500, -100, 5],
             'rec': [0, 1000, 20],
             'res': 6.71,
             'aniso': 1.2,
             'freqtime': -1,
             'signal': None,
             'ab': 12,
             'verb': 0}
    # Check dhs, dsplit, and dtetm
    ana_res = analytical(solution='dhs', **model)
    res1, res2, res3 = analytical(solution='dsplit', **model)
    dTE, dTM, rTE, rTM, air = analytical(solution='dtetm', **model)
    model['res'] = [2e14, model['res']]
    model['aniso'] = [1, model['aniso']]
    dip_res = dipole(depth=0, **model)
    # Check dhs, dsplit
    assert_allclose(dip_res, ana_res, rtol=1e-3)
    assert_allclose(ana_res, res1+res2+res3)
    # Check dsplit and dtetm
    assert_allclose(res1, dTE+dTM)
    assert_allclose(res2, rTE+rTM)
    assert_allclose(res3, air)

    # 3. Check user-hook for eta/zeta
    def func_eta(inp, pdict):
        # Dummy function to check if it works.
        etaH = pdict['etaH'].real*inp['fact'] + 1j*pdict['etaH'].imag
        etaV = pdict['etaV'].real*inp['fact'] + 1j*pdict['etaV'].imag

        return etaH, etaV

    def func_zeta(inp, pdict):
        # Dummy function to check if it works.
        etaH = pdict['zetaH']/inp['fact']
        etaV = pdict['zetaV']/inp['fact']

        return etaH, etaV

    model = {'src': [0, 0, 500], 'rec': [500, 0, 600],
             'freqtime': [0.1, 1, 10]}
    res = 10
    fact = 2
    eta = {'res': fact*res, 'fact': fact, 'func_eta': func_eta}
    zeta = {'res': res, 'fact': fact, 'func_zeta': func_zeta}

    # Frequency domain fs
    standard = analytical(res=res, **model)
    outeta = analytical(res=eta, **model)
    assert_allclose(standard, outeta)
    outzeta = analytical(res=zeta, mpermH=fact, mpermV=fact, **model)
    assert_allclose(standard, outzeta)
    # Time domain dhs
    standard = analytical(res=res, solution='dhs', signal=0, **model)
    outeta = analytical(res=eta, solution='dhs', signal=0, **model)
    assert_allclose(standard, outeta)
    outzeta = analytical(res=zeta, solution='dhs',
                         signal=0, mpermH=fact, mpermV=fact, **model)
    assert_allclose(standard, outzeta)


def test_gpr(capsys):
    # empymod is not really designed for GPR, you would rather do that straight
    # in the time domain. However, it works. We just run a test here, to check
    # that it remains the status quo.
    res = DATAEMPYMOD['gprout'][()]
    gprout = gpr(**res['inp'])
    out, _ = capsys.readouterr()
    assert 'GPR' in out
    assert '> centre freq :  250000000' in out
    assert_allclose(gprout, res['GPR'])
    # Ensure multi-source/receiver is correct (reshaping after dipole-call)
    gprout2a = gpr(**res['inp2a'])
    gprout2b = gpr(**res['inp2b'])
    assert_allclose(gprout[:, :, 1], gprout2a)
    assert_allclose(gprout[:, 0, :], gprout2b)


def test_dipole_k():
    # This is like `frequency`, without the Hankel transform. We just run a
    # test here, to check that it remains the status quo.
    res = DATAEMPYMOD['wout'][()]
    w_res0, w_res1 = dipole_k(**res['inp'])
    assert_allclose(w_res0, res['PJ0'])
    assert_allclose(w_res1, res['PJ1'])

    # Check that ab=36 returns zeros
    res['inp']['ab'] = 36
    w_res0, w_res1 = dipole_k(**res['inp'])
    assert_allclose(w_res0, np.zeros(res['PJ0'].shape, dtype=np.complex128))
    assert_allclose(w_res1, np.zeros(res['PJ1'].shape, dtype=np.complex128))


def test_ip_and_q(capsys):
    # Very simple tests; the function is only a wrapper, so we just test
    # the functionality.

    # Status Quo
    system = {
        "src": [0, 0, -1],
        "rec": [2, 0, -1],
        "freqtime": [1.0, 100.0, 10000.0],
        "ab": 66,
        "verb": 1,
    }

    model1 = {
        "depth": [0, 2, 5],
        "res": [2e14, 50, 0.1, 50],
        "aniso": [1, 1.2, 1, 1],
        "epermH": [0, 1, 1.1, 1],
        "epermV": [0, 1, 1, 1.1],
        "mpermH": [1, 1, 1.5, 1],
        "mpermV": [1, 1.1, 1, 1],
    }

    IP1, Q1 = model.ip_and_q(**model1, **system)
    assert_allclose(IP1, [-8.03041994, -7.929775, 18.53988624])
    assert_allclose(Q1, [0.0126156904, 1.23806259, 16.3291884])

    IP2, Q2 = model.ip_and_q(**model1, **system, scale=1e6)
    assert_allclose(IP1*1e3, IP2)
    assert_allclose(Q1*1e3, Q2)

    IP3, Q3 = model.ip_and_q(**model1, **{**system, 'ab': 44})
    assert_allclose(IP3, [-1.3563986, -1.38122726, -7.4560389])
    assert_allclose(Q3, [-0.00299279869, -0.293418700, -3.40236993])

    IP4, Q4 = model.ip_and_q(**model1, **{**system, 'ab': 55})
    assert_allclose(IP4, [-10.74321713, -10.69222953, 3.62780845])
    assert_allclose(Q4, [0.00663009305, 0.651225190, 9.52444857])

    # Test errors
    with pytest.raises(ValueError, match="Only implemented for magnetic"):
        model.ip_and_q(**model1, **{**system, "ab": 13})

    with pytest.raises(ValueError, match="Only implemented for frequency"):
        model.ip_and_q(**model1, **{**system, "signal": 0})

    with pytest.raises(ValueError, match="Only implemented for frequency"):
        model.ip_and_q(**model1, **{**system, "signal": 1})

    # Fullspace - no secondary field -> zeros
    model2 = {"depth": [0], "res": [50, 50]}
    IP5, Q5 = model.ip_and_q(**model2, **system)
    assert_allclose(IP5, 0.0)
    assert_allclose(Q5, 0.0)

    _, _ = capsys.readouterr()
    _, _ = model.ip_and_q(**model1, **{**system, "src": [0, 0, 0]})
    out, _ = capsys.readouterr()
    assert "This function is experimental" in out


def test_fem():
    # Just ensure functionality stays the same, with one example.
    for i in ['1', '2', '3', '4', '5']:
        res = DATAFEMTEM['out'+i][()]
        fEM, kcount, _ = fem(**res['inp'])
        assert_allclose(fEM, res['EM'])
        assert kcount == res['kcount']


def test_tem():
    # Just ensure functionality stays the same, with one example.
    for i in ['6', '7', '8']:  # Signal = 0, 1, -1
        res = DATAFEMTEM['out'+i][()]
        tEM, _ = tem(**res['inp'])
        assert_allclose(tEM, res['EM'])

    # Test `xdirect=None` through analytical/dipole-comparison with a simple
    # model

    # Fullspace model
    inp = {'src': [[0, -100], [0, -200], 200],
           'rec': [np.arange(1, 11)*500, np.arange(1, 11)*100, 300],
           'freqtime': [0.1, 1, 10], 'res': 1}
    fEM_fs = analytical(**inp)

    # Add two layers
    inp['depth'] = [0, 500]
    inp['res'] = [10, 1, 30]
    fEM_tot1 = dipole(xdirect=False, **inp)
    fEM_tot2 = dipole(xdirect=True, **inp)
    fEM_secondary = dipole(xdirect=None, **inp)

    # `xdirect=False` and `xdirect=True` have to agree
    assert_allclose(fEM_tot2, fEM_tot1)

    # Total field minus minus direct field equals secondary field
    assert_allclose(fEM_tot1 - fEM_fs, fEM_secondary)


def test_regres():
    # Comparison to self (regression test)
    # 1836 cases; f = [0.01, 1, 100] Hz.; 18 models, 34 ab's, f altern.
    dat = REGRES['res'][()]
    for _, val in dat.items():
        res = dipole(**val[0])
        assert_allclose(res, val[1], 3e-2, 1e-17, True)


class TestSqueeze:

    def test_bipole(self):
        inp = {'src': [0, 0, 0, 0, 0], 'rec': [1000, 2000, 300, 0, 0],
               'freqtime': 1.0, 'depth': [], 'res': 1.0}

        a = bipole(**inp)
        b = bipole(squeeze=False, **inp)

        assert a.shape == ()
        assert b.shape == (1, 1, 1)

    def test_dipole(self):
        inp = {'src': [0, 0, 0], 'rec': [1000, 2000, 300],
               'freqtime': [0.1, 1.0], 'depth': [], 'res': 1.0}

        a = dipole(**inp)
        b = dipole(squeeze=False, **inp)

        assert a.shape == (2, )
        assert b.shape == (2, 1, 1)

    def test_loop(self):
        inp = {'src': [[0, 10], [0, 0], 0, 0, 0],
               'rec': [1000, 2000, 300, 0, 0],
               'freqtime': 1.0, 'depth': [], 'res': 1.0}

        a = loop(**inp)
        b = loop(squeeze=False, **inp)

        assert a.shape == (2, )
        assert b.shape == (1, 1, 2)

    def test_analytical(self):
        inp = {'src': [0, 0, 0], 'rec': [[1000, 2000], [2000, 2000], 300],
               'freqtime': 1.0, 'res': 1.0}

        a = analytical(**inp)
        b = analytical(squeeze=False, **inp)

        assert a.shape == (2, )
        assert b.shape == (1, 2, 1)


def test_all_dir():
    assert set(model.__all__) == set(dir(model))
