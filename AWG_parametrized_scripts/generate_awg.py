import si_fab.all as pdk
from luceda.octopic.visualize import visualize
from si_fab_awg.all import SiSlabTemplate, SiRibAperture, SiRibMMIAperture
from picazzo3.container.fanout_ports import FanoutPorts
from picazzo3.container.iofibcoup import IoFibcoup
import awg_designer.all as awg
import ipkiss3.all as i3
import numpy as np
import matplotlib.pyplot as plt
import json
import os
import MRT_PDK_extension.all as cc


# Set here if you want the output spectrum to be plotted.
# You may decide to have other booleans to toggle different things on and off.
plot = True

##############################################################
#       Provide Functional Specifications for your AWG       #
##############################################################

# Set your desired center frequency.
center_wavelength = 1.550  # um

# Set the desired spacing between wavelength channels.
channel_spacing = (6.41e-3) #(6.41e-3)*2 #um #800.0  # units in GHz
#print(awg.frequency_to_wavelength(channel_spacing))

# Set your desired number of wavelength channels:
n_channels = 16

# Set your desired Free Spectral Range.
fsr = (n_channels + 6) * channel_spacing

###############################################
#       Provide Physical Specifications       #
###############################################

# Minimum spacing between the output apertures (center-to-center).
# Increasing this value means less crosstalk but more power lost between the two channels.
output_aperture_spacing = 18.0

# This value affects the angular spread of the output apertures.
fpr_alpha_factor = 1.6

# Set your desired number of arrayed waveguide arms.
# Default is None for an automatic number of arms.
n_arms = None

##################################################
#     Provide Central array Specifications       #
##################################################
central_array_S_shaped = False
star_coupler_separation = 6000 #5500 #8500 #6000
star_coupler_rotation = 20 #10 #30 #20
extra_length = 50#20 #80 #50
if central_array_S_shaped:
    bundle_shape = "S_array"
if not central_array_S_shaped:
    bundle_shape = "parabolic_array"

##################################################
#      Provide Subcomponent Specifications       #
##################################################

# Set your desired waveguide core width, determined by your pdk.
wg_width = pdk.TECH.MRTWG.CORE_WIDTH  # units in um
cladding_width = pdk.TECH.MRTWG.CLADDING_WIDTH
ap_extension = (cladding_width/2)+0.25

#####################################################
#       Provide Implementation Specifications       #
#####################################################

# Add dummies to input and output ports of the Star Couplers.
# Typically, you want at least two dummies.
n_dummies = 2

#########################################
#       Simulation Specifications       #
#########################################

# The parameters here sets the simulation range for the AWG and subcomponents,
# the third entry in np.linspace is the amount of samples or step
# in wavelength that you want the simulation to take.

# The wavelengths at which the slab modes are simulated.
simulation_wavelengths_slab = np.linspace(1.40, 1.70, 1000)

# The wavelengths at which the apertures and star coupler are simulated.
# Either the same wavelengths as the slab or only one wavelength to reduce simulation time.

# The wavelengths at which the total AWG is simulated.
sim_start = center_wavelength - fsr/2 - channel_spacing
sim_end   = center_wavelength + fsr/2 + channel_spacing
simulation_wavelengths_awg = np.linspace(sim_start, sim_end, 2000)
visualize_modes= False

#######################################
#       Analysis Specifications       #
#######################################

# You can raise or lower the peak_threshold as you see fit.
# Note that the higher the value the less likely you will register weak signals.
peak_threshold = -4  # units in dB

###########################################
#       Create a folder for results       #
###########################################

this_dir = os.path.abspath(os.path.dirname(__file__))
designs_dir = os.path.join(this_dir, "designs")
if not os.path.exists(designs_dir):
    os.mkdir(designs_dir)
save_dir = os.path.join(designs_dir, f"Final_design_awg_{bundle_shape}_CW_{center_wavelength}um_channel_spacing_{channel_spacing*10**3}nm_fsr{fsr*10**3}nm")
if not os.path.exists(save_dir):
    os.mkdir(save_dir)

#########################################
#       Instantiate subcomponents       #
#########################################

print("Instantiating subcomponents...\n")

# Use the slab template from PDK.
slab = cc.Mat1SlabTemplate()

# Calculate the slab modes with CAMFR.
slab_modes = slab.SlabModesFromCamfr(wavelengths=simulation_wavelengths_slab)
if visualize_modes:
    slab_modes.visualize(wavelengths=simulation_wavelengths_slab)

# Use aperture templates from the PDK. We use a standard rib aperture for the outputs and arms.
aperture = cc.ExitAperture(slab_template=slab)

# Simulate the aperture at only the center length to save on computation time.
aperture.CircuitModel(simulation_wavelengths=[center_wavelength])
if visualize_modes:
    fieldmodel = aperture.FieldModelFromCamfr()
    fields_1d = fieldmodel.get_fields(
       mode=0, environment=i3.Environment(wavelength=center_wavelength)
    )
    fields_1d.visualize()

# You can use an MMI aperture for the input. This creates a broad transmission band for the frequency channels.
aperture_mmi = cc.InputAperture(slab_template=slab)
aperture_mmi.CircuitModel(simulation_wavelengths=[center_wavelength])
if visualize_modes:
    fieldmodel_mmi = aperture_mmi.FieldModelFromCamfr()
    fields_1d_mmi = fieldmodel_mmi.get_fields(
       mode=0, environment=i3.Environment(wavelength=center_wavelength)
    )
    fields_1d_mmi.visualize()

# Use the waveguide template from the PDK
wg_tmpl = cc.MRTWaveguideTemplate()
wg_tmpl.Layout(core_width=wg_width)

##################################
#       Synthesize the AWG       #
##################################

print("\nDeriving implementation parameters...\n")

design_params = awg.get_layout_params_1xM_demux_um(
    aperture_in=aperture_mmi,
    aperture_arms=aperture,
    aperture_out=aperture,
    waveguide_template=wg_tmpl,
    output_spacing=output_aperture_spacing,
    alpha_factor=fpr_alpha_factor,
    M=n_channels,
    N_arms=n_arms,
    center_wavelength=center_wavelength,
    channel_spacing=channel_spacing,
    FSR=fsr,
    grating_period=7.8, #6.8
    verbose=True,
)

# Print output
print("\nDesign parameters:\n")

if plot:
    print(design_params)


# Saving design parameters
def serialize_ndarray(obj):
    return obj.tolist() if isinstance(obj, np.ndarray) else obj


json_path = os.path.abspath(os.path.join(save_dir, "design_params.json"))
with open(json_path, "w") as f:
    json.dump(design_params, f, sort_keys=True, default=serialize_ndarray, indent=0)
print(f"{json_path} written")

# Retrieve implementation parameters
angles_arms_out = design_params["angles_arms_out"]  # For grating arms
angles_arms_in = design_params["angles_arms_in"]  # For grating arms
angles_out = design_params["angles_out"]  # For I/O waveguides to rest of chip
angles_in = np.array([0.0])  # Setting the angle in equal to 0
grating_radius_output = design_params["R_grating"]  # For output grating coupler
grating_radius_input = design_params["R_input"]  # For input grating coupler
n_arms = design_params["N_arms"]  # Number of arms, or delay waveguides in the grating
delay_length = design_params["delay_length"]  # Delay length for a single arm

#######################################
#         Output star coupler         #
#######################################

print("Defining output star coupler...\n")

# Set the apertures (sc_out_array) and their angles (sc_out_array_angles) together with dummy apertures.
# This is for the grating arms/waveguides.
sc_out_array, sc_out_array_angles = awg.get_apertures_angles_with_dummies(
    apertures=[aperture] * n_arms,
    angles=angles_arms_out,
    n_dummies=n_dummies,
)

# Set the apertures (sc_out_ports) and their angles (sc_out_ports_angles).
# This is for the I/O waveguides to the rest of the chip.
sc_out_ports, sc_out_ports_angles = awg.get_apertures_angles_with_dummies(
    apertures=[aperture] * len(angles_out),
    angles=angles_out,
    n_dummies=n_dummies,
)

# Generate aperture mounting
(
    sc_out_array_aperture,  # The MultiAperture on the arm/array side, of the chosen MultiAperture type
    sc_out_ports_aperture,  # The MultiAperture on the ports side, of the chosen MultiAperture type
    sc_out_array_xforms,  # The transformations of the arm/array apertures
    sc_out_ports_xforms,  # The transformations of the ports apertures
) = awg.get_star_coupler_apertures(
    apertures_arms=sc_out_array,  # The apertures for grating arms
    apertures_ports=sc_out_ports,  # The ports for I/O arms
    angles_arms=sc_out_array_angles,  # The angles for grating arms
    angles_ports=sc_out_ports_angles,  # The angles for I/O arms
    radius=grating_radius_output,  # Grating radius for the star coupler
    mounting="rowland",  # Rowland mounting for the aperture (refer to documentation for details)
    input=False,  # True if the star coupler is an input star coupler, False if it's an output star coupler
)

# Generate free propagation contour around the slab region.
# This will be used as an input in the next step to generate the star coupler.
contour = awg.get_star_coupler_extended_contour(
    apertures_in=sc_out_array,
    apertures_out=sc_out_ports,
    trans_in=sc_out_array_xforms,
    trans_out=sc_out_ports_xforms,
    radius_in=grating_radius_output,
    radius_out=grating_radius_output * 0.5,
    extension_angles=(10, 10),
    aperture_extension=(0.0, ap_extension)
)

# Compose the star coupler.
sc_out = awg.StarCoupler(
    aperture_in=sc_out_array_aperture,
    aperture_out=sc_out_ports_aperture,
)
sc_out.Layout(contour=contour)
sc_out.CircuitModel(simulation_wavelengths=[center_wavelength])
sc_out_layout = sc_out.Layout(contour=contour)
if central_array_S_shaped:
    sc_out_layout.visualize(annotate=True)

######################################
#         Input star coupler         #
######################################

print("Defining input star coupler...\n")
sc_in_array, sc_in_array_angles = awg.get_apertures_angles_with_dummies(
    apertures=[aperture] * n_arms, angles=angles_arms_in, n_dummies=n_dummies
)
sc_in_ports, sc_in_ports_angles = awg.get_apertures_angles_with_dummies(
    apertures=[aperture_mmi] * len(angles_in),
    angles=angles_in,
    n_dummies=n_dummies,
    angle_step=2.0,
)
(sc_in_array_aperture, sc_in_ports_aperture, sc_in_array_xforms, sc_in_ports_xforms) = awg.get_star_coupler_apertures(
    apertures_arms=sc_in_array,
    apertures_ports=sc_in_ports,
    angles_arms=sc_in_array_angles,
    angles_ports=sc_in_ports_angles,
    radius=grating_radius_input,
    mounting="rowland",
    input=True,
)

contour = awg.get_star_coupler_extended_contour(
    apertures_in=sc_in_ports,
    apertures_out=sc_in_array,
    trans_in=sc_in_ports_xforms,
    trans_out=sc_in_array_xforms,
    radius_in=grating_radius_input * 0.5,
    radius_out=grating_radius_input,
    extension_angles=(10, 10),
    aperture_extension=(ap_extension, 0.0)
)

sc_in = awg.StarCoupler(
    aperture_in=sc_in_ports_aperture,
    aperture_out=sc_in_array_aperture,
)

sc_in_layout = sc_in.Layout(contour=contour)
sc_in.CircuitModel(simulation_wavelengths=[center_wavelength])
if central_array_S_shaped:
    sc_in_layout.visualize(annotate=True)

###################################
#         Waveguide array         #
###################################
if not central_array_S_shaped:
    star_coupler_separation = star_coupler_separation
    star_coupler_rotation = star_coupler_rotation
    extra_length = extra_length
    # layout parameters setting
    x_offset = (
        sc_in_layout.ports.x_sorted()[-1].position[0]
        - sc_out_layout.ports.x_sorted()[0].position[0]
    )

    rotation_center = (
        0.5 * sc_in_layout.ports.x_sorted()[-1].position
        + 0.5 * sc_out_layout.ports.x_sorted()[0].position
    )

    sc_out_xform = i3.Translation(
        translation=(star_coupler_separation / 2.0 + x_offset / 2.0, 0.0)
    ) + i3.Rotation(rotation_center=rotation_center, rotation=-star_coupler_rotation)

    sc_in_xform = i3.Translation(
        translation=(-star_coupler_separation / 2.0 - x_offset / 2.0, 0.0)
    ) + i3.Rotation(rotation_center=rotation_center, rotation=star_coupler_rotation)

    from ipkiss3.pcell.container.container import _Container

    sc_in_new = _Container(contents=sc_in)
    sc_in_new_layout = sc_in_new.Layout(contents_transformation=sc_in_xform)
    sc_in_new_layout.visualize(annotate=True)

    sc_out_new = _Container(contents=sc_out)
    sc_out_new_layout = sc_out_new.Layout(contents_transformation=sc_out_xform)
    sc_out_new_layout.visualize(annotate=True)

    bundle_in_ports = sc_in_new_layout.east_ports.y_sorted()
    bundle_out_ports = sc_out_new_layout.west_ports.y_sorted()
    print("Creating self defined waveguide array...\n")
    # Define the delay lengths based on previously calculated delay.
    min_length = bundle_in_ports[0].position.distance(bundle_out_ports[0]) + extra_length
    delays = [min_length + delay_length * i for i in range(len(bundle_out_ports))]
    print("delay lengths:")
    print(delays)


    waveguides = cc.get_bundle(
        start_ports=bundle_in_ports,
        end_ports=bundle_out_ports,
        delay_lengths=delays,
        trace_template=wg_tmpl,
    )

    # create a bundle
    from picazzo3.wg.bundle import WaveguideBundle

    bundle = WaveguideBundle(traces=waveguides)
    #bundle.Layout(cover_layers=[]).visualize(annotate=True)




if central_array_S_shaped:
    print("Creating S-shaped waveguide array...\n")
    delays = [delay_length * i for i in range(n_arms)]
    print("delay lengths:", delays)
    wg_array = awg.SWaveguideArray(
        start_ports=sc_in_layout.east_ports.y_sorted(),
        delay_lengths=delays,
    )
    wg_array.Layout(
        offset_output_ports_south=80.0,
        route_properties={
            "rounding_algorithm": i3.SplineRoundingAlgorithm(adiabatic_angles=(15.0, 15.0)),
            "bend_radius": 1500.0,
        },
    )



##################################
#         Create the AWG         #
##################################

print("Creating AWG...\n")

if not central_array_S_shaped:
    generated_awg = awg.ArrayedWaveguideGrating(
        star_coupler_in=sc_in_new.contents,
        star_coupler_out=sc_out_new.contents,
        waveguide_array=bundle,
    )
if central_array_S_shaped:
    generated_awg = awg.ArrayedWaveguideGrating(
        star_coupler_in=sc_in,
        star_coupler_out=sc_out,
        waveguide_array=wg_array,
    )

generated_awg_layout = generated_awg.get_default_view(i3.LayoutView)
generated_awg_netlist = generated_awg.get_default_view(i3.NetlistView)
generated_awg_circuit = generated_awg.get_default_view(i3.CircuitModelView)
generated_awg_layout.visualize(annotate=True)

gds_path = os.path.abspath(os.path.join(save_dir, "layout.gds"))
generated_awg_layout.write_gdsii(gds_path)

##############################
#      Simulate the AWG      #
##############################

print("Simulating AWG...")
awg_s = generated_awg_circuit.get_smatrix(simulation_wavelengths_awg)  # Note, fanout not simulated
term_pairs = [("in1", f"out{i}") for i in range(1, n_channels + 1)]
awg_s.visualize(term_pairs=term_pairs, scale="dB")
smatrix_path = os.path.join(save_dir, f"smatrix.s{awg_s.data.shape[0]}p")
awg_s.to_touchstone(smatrix_path)
print(f"{smatrix_path} written")

#############################
#      Analyse the AWG      #
#############################

# Calculate the frequencies of the different channels.
channel_half_span = channel_spacing * (n_channels - 1) / 2
channel_wav = np.linspace(center_wavelength - channel_half_span, center_wavelength + channel_half_span, n_channels)


channel_width = 10e-4
margin = 0.008
output_ports = [f"out{p + 1}" for p in range(len(channel_wav))]


print("Analyzing AWG...")
# Initialize spectrum analyzer
spec_analyzer = i3.SpectrumAnalyzer(
    smatrix=awg_s,
    input_port_mode="in1:0",
    output_port_modes=output_ports,
    dB=True,
    peak_threshold=peak_threshold,
)

# Trim the x-axis of the spectrum analyzer
spec_analyzer = spec_analyzer.trim(
    (
        min(channel_wav) - channel_width-margin,
        max(channel_wav) + channel_width+margin,
    )
)

####################################
#      Measure key parameters      #
####################################

print("Measuring Peaks...")
peaks = spec_analyzer.peaks()
print(peaks)
peak_wavelengths = [peak["wavelength"][0] for peak in peaks.values()][::-1]
print(channel_wav)
print(peak_wavelengths)
peak_error = np.abs(channel_wav - peak_wavelengths)
print(peak_error)

print("Measuring Crosstalk Bands...")
bands = spec_analyzer.width_passbands(channel_width)
insertion_loss = list(spec_analyzer.min_insertion_losses(bands=bands).values())
cross_talk_near = list(spec_analyzer.near_crosstalk(bands=bands).values())
cross_talk_far = list(spec_analyzer.far_crosstalk(bands=bands).values())
passbands_3dB = list(spec_analyzer.cutoff_passbands(cutoff=-3.0).values())

###################################
#      Write Analysis report      #
###################################

report = dict()
band_values = list(bands.values())
for cnt, port in enumerate(output_ports):
    channel_report = {
        "peak_expected": channel_wav[cnt],
        "peak_simulated": peak_wavelengths[cnt],
        "peak_error": peak_error[cnt],
        "band": band_values[cnt][0],
        "insertion_loss": insertion_loss[cnt][0],
        "cross_talk": cross_talk_far[cnt] - insertion_loss[cnt][0],
        "cross_talk_nn": cross_talk_near[cnt] - insertion_loss[cnt][0],
        "passbands_3dB": passbands_3dB[cnt],
    }
    report[port] = channel_report


def serialize_ndarray(obj):
    return obj.tolist() if isinstance(obj, np.ndarray) else obj


report_path = os.path.join(save_dir, "report.json")

# open file for writing, "w"
with open(report_path, "w") as f:
    json.dump(report, f, default=serialize_ndarray, indent=0) #json.dump(report, f, sort_keys=True, default=serialize_ndarray, indent=0)
print(f"{report_path} written")

##################################
#         Plot Spectrum          #
##################################

if plot:
    print("Plotting Spectrum...")
    fig = spec_analyzer.visualize(title="Output spectrum of AWG", show=False)
    for spec_wavelength in channel_wav:
        plt.axvline(x=spec_wavelength)

    for passband in passbands_3dB:
        plt.axvline(x=passband[0][0], color="k", linestyle=":")
        plt.axvline(x=passband[0][1], color="k", linestyle=":")

    plt.xlabel(r"Wavelength [$\mu$m]")

    fig.savefig(os.path.join(save_dir, "output_spectrum.png"), bbox_inches="tight")

    # Plot transmission spectrum
    plt.show()

print("Complete...")

#####################################
#           Finalize AWG            #
#####################################





from picazzo3.container.route_ports import RoutePortsEastWest
from ipkiss3.pcell.container.container import _Container
# # Wrap in a cell with a clean layout
awg_clean_layout = generated_awg_layout.layout.flat_copy()
awg_clean = i3.EmptyCell(name="awg_clean")
awg_clean.Layout(layout=awg_clean_layout, ports=generated_awg_layout.ports)
awg_clean.Netlist(terms=generated_awg_netlist.terms)
awg_clean.CircuitModel(model=generated_awg_circuit.model)
ports = [p for p in generated_awg_layout.ports if "out" in p.name]
input_ports = [p for p in generated_awg_layout.ports if "in" in p.name]


wg_tmpl = cc.MRTWaveguideTemplate()
cell = _Container(contents=awg_clean)
#xform = i3.Translation(translation=-cell.Layout().size_info().center) + i3.Rotation(rotation_center=(0,0), rotation=20)
cell_lo = cell.Layout()#cell.Layout(contents_transformation=xform)

y_spacing_between_adjacent_wgs =100
routed_awg = RoutePortsEastWest(
    contents=cell_lo,
    east_port_labels=[f'out{t+1}' for t in range(len(cell_lo.east_ports))],  # ports to be routed eastward
    west_port_labels=[t.name for t in cell_lo.west_ports],  # ports to be routed westward
    trace_template=wg_tmpl,
)
awg_routed_layout = routed_awg.Layout(target_coordinate_east=8000.0, target_coordinate_west=-8000.0,
                           bend_radius=1500,
                           spacing=y_spacing_between_adjacent_wgs)
awg_routed_layout.visualize()


class IoFibcoup1550(IoFibcoup):
    def _default_trace_template(self):
        return wg_tmpl
    def _default_fiber_coupler(self):
        return cc.MRT_FC_TE_1550()

awg_block = i3.IoColumn(name="test design awg" , adapter=IoFibcoup1550)
awg_block_layout = awg_block.Layout(
    south_west=(-12000.0, 0),
    south_east=(12000.0,  0),
    y_spacing=y_spacing_between_adjacent_wgs, )

awg_block.add_blocktitle(f"AWG_CW_{center_wavelength}um_channel_spacing_{channel_spacing*10**3}nm_fsr{fsr*10**3}nm")
awg_block.add_align(trace_template=wg_tmpl)
awg_block.add_emptyline(8)
awg_block.add(
    routed_awg,
    relative_offset=(0.0, (awg_routed_layout.ports["in1"].y - awg_routed_layout.ports["out1"].y)),
    bend_radius= 1500
    )


#Plotting and writing to gds.
if plot:
    awg_block_layout.visualize(annotate=True)

# Save to GDS directly
gds_path = os.path.abspath(os.path.join(save_dir, "awg_layout_finalized.gds"))
awg_block_layout.write_gdsii(gds_path)
print(f"{gds_path} written.")