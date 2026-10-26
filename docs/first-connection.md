# First vehicle session

## Before connecting

1. Record the car's model year, engine and intake/exhaust changes, injectors,
   forced induction if any, fuel grade, known faults, and tuning goals in
   `vehicle.json`. Record whether its present tune is known stock or unknown.
2. Connect the MPVI4 to the Focus diagnostic connector and the laptop by USB.
3. For the initial identification/read, use ignition on with engine off and
   follow VCM Editor's prompts. Maintain adequate battery power for the session.

## Identify and preserve

1. Record the connected vehicle VIN, controller type, operating system and
   calibration identifiers privately under `.local/`. Compare the VIN/controller
   with the existing interface license before purchasing or allocating credits.
2. Use VCM Editor's vehicle **Read** function if the controller is supported.
   Save the untouched result under `backups/` with a timestamp and the word
   `original`. Call it stock only if its stock status is established; a first
   read may contain a previous owner's tune.
3. Preserve the original read and its SHA-256 hash. Make a separate working copy
   under `tunes/` before editing anything. Keep another backup outside this repo.
4. Record diagnostic trouble codes in VCM Scanner before clearing anything.

## Collect an initial scan

Once the car's condition permits running, use VCM Scanner to inspect available
channels. Channel names and availability depend on this controller. Start with
RPM, coolant and intake temperatures, battery voltage, throttle, vehicle speed,
MAF/load, short- and long-term fuel trims, commanded fueling, ignition timing,
and available oxygen-sensor feedback. Add knock information only if supported.

Capture a warm idle baseline first. Later light-load logs should record the
fuel, ambient conditions, engine state, symptoms, and calibration filename.
Save native recordings and export CSV where available under `logs/`.
Do not interpret a narrowband oxygen-sensor signal as measured wideband AFR.

Choose tuning changes after reviewing the original calibration, faults, and
baseline data. No flash or calibration changes are part of this first setup.
