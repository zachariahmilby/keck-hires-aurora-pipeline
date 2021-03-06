from pathlib import Path

import astropy.units as u

from khan.analysis.brightness_retrieval import OrderData, Background, \
    AuroraBrightness
from khan.analysis.quality_assurance import \
    make_background_subtraction_quality_assurance_graphic, \
    make_1d_spectrum_quality_assurance_graphic
from khan.common import aurora_line_wavelengths, \
    emission_line_strengths

import warnings


def get_aurora_brightnesses(reduced_data_path: str | Path,
                            save_path: str | Path,
                            seeing: float = 1,
                            exclude: dict = None,
                            y_offset: int = 0,
                            top_trim: int = 2,
                            bottom_trim: int = 2,
                            additional_wavelengths: bool = False):
    """
    Retrieve the brightnesses for any auroral lines which appear in the
    extracted orders. Saves data to the file for plotting or other purposes and
    also saves a text file of the results.

    Parameters
    ----------
    reduced_data_path : str or Path
        The location of the pipeline output files "flux_calibration.fits.gz"
        and "science_observations.fits.gz".
    save_path : str or Path
        The location where you want the retrieved brightnesses saved.
    seeing : float
        How much to add to the radius of the of the target in arcseconds to
        account for atmospheric seeing or other point-source smearing effects.
    exclude : dict
        Frames to exclude from the calcualtion of the average. The dictionary
        keys need to be the average wavelength of the aurora line to one
        decimal place, e.g., '630.0 nm' or '777.4 nm'. The values should be
        a list or array of the indices of the frames to exclude, starting from
        zero, e.g., to exclude the first three frames the list should be
        [0, 1, 2]. You only need to include keys and values for wavelengths
        which have values you want to exclude. If there aren't any for, say,
        630.0 nm, don't add a key or value for it.
    y_offset: int
        Number of bins to offset the center of the aperture from the center
        of the order. Useful if the spatial position of the target isn't in
        the exact center.
    top_trim: int
        How many rows to remove from the top edge of the order to eliminate
        artifacts from rectification. Default is 2.
    bottom_trim: int
        How many rows to remove from the bottom edge of the order to
        eliminate artifacts from rectification. Default is 2.
    additional_wavelengths : bool
        Set to true if you want to (attempt to) retrieve brightnesses for
        additional auroral lines.

    Returns
    -------
    None. But it makes many output files.
    """

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wavelengths = aurora_line_wavelengths(extended=additional_wavelengths)
        line_strengths = emission_line_strengths(
            extended=additional_wavelengths)
        for i in range(len(wavelengths)):
            try:
                order_data = OrderData(
                    reduced_data_path=reduced_data_path,
                    wavelengths=wavelengths[i],
                    emission_line_strengths=line_strengths[i],
                    seeing=seeing * u.arcsec,
                    exclude=exclude, top_trim=top_trim,
                    bottom_trim=bottom_trim)
                background = Background(order_data=order_data,
                                        y_offset=y_offset)
                aurora_brightness = AuroraBrightness(order_data=order_data,
                                                     background=background,
                                                     save_path=save_path)
                make_background_subtraction_quality_assurance_graphic(
                    order_data=order_data, background=background,
                    save_path=save_path, y_offset=y_offset)
                aurora_brightness.save_results()
                make_1d_spectrum_quality_assurance_graphic(
                    save_path=save_path, order_data=order_data)
            except ValueError:
                print(f'{wavelengths[i].mean():.1f} not found! Skipping...')
                continue
