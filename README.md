# CIRS Geometric Distortion Platform

## System Dependencies

- Python 3.6
- Redis
- Postgres
- Linux utilities (e.g. Make)
- Lib HDF5

You can install all of these using homebrew pretty easily on mac.

## Hot Module Replacement

You can enable hot module replacement using:

    yarn run build:hot

## Python Path

Note, in order to run python tests or scripts, you will need to be sure that the root of the repository is on the PYTHONPATH.

You can set by running:

    export PYTHONPATH=.

from the root of the repository.

## Creating a demo database on Heroku

First, make sure you have a fresh database.  You can reset it from the Heroku database web UI (I have not been able to get it to work from the CLI for some reason).

Next, grab all of the Heroku settings and put them in your `.env` file (be sure to swap back to the development `.env` file when you are done).

Then run `manage.py migrate` and `manage.py generate_demo_data` from your local dev machine; since you have the demo environment variables set, it will generate the demo data and place it in S3 and in the database.

NOTE: you can not use a Heroku one-off dyno for this, since some of the DICOM files needed for the `generate_demo_data` script are excluded from the slug for size reasons.

## Interactive Algorithm Work

You will need to swap out the matplotlib backend for interactive algorithm
work; see `matplotlibrc` for details.

## End-to-End Tests

1. Navigate to https://tools.cirsinc.com/.
2. Click on "Register New Account."
3. Input one of "SN3" through "SN14" for the "Phantom Serial Number" and verify that the model number is shown.
4. Fill out the rest of the form, using an email address that you have access to.
5. Click on the link in the email sent to you to create your password.
6. Create your password, and login.
7. Logout.
8. Click on "Forgot your Password?"
9. Enter your email.
10. Click on the link in the email sent to you to reset your password.
11. Reset your password, and login.
12. Navigate to "Configuration."
13. Edit the institution info, and verify that it's updated.
14. Click on "Add Phantom" and fill out the form. For the serial number, use one of "SN3" through "SN14", other than the one you used to register.
15. Verify that the new phantom is listed in the phantom table.
16. Click on "Edit" on the new phantom row.
17. Change the name, and verify that the name is updated.
18. Click on "Upload Gold Standard CT."
19. Choose `data/dicom/001_ct_603A_E3148_ST1.25.zip`.
20. Wait until the data is finished processing.
21. Click on "Download Images" and "Download Points" on the new gold standard row.
22. Click on "Set Active" on the new gold standard row and verify that it becomes the active gold standard, or else shows an error.
23. Set the CAD gold standard back to active, and click on the trashcan on the new gold standard row to delete it.
24. Click on "Upload Raw Points."
25. Upload `data/example_points_upload.csv`; try setting it to "active" and verify that no error message is shown and that it is set to active.
26. Navigate back to "Configuration" and delete the new phantom.
27. Click on "Add Machine" and fill out the form.
28. Click on "edit" on the new machine row, change the info, and verify that it's updated.
29. Navigate back to "Configuration" and delete the new machine.
30. Click on "Add Sequence" and fill out the form.
31. Click on "edit" on the new sequence row, change the info, and verify that it's updated.
32. Navigate back to "Configuration" and delete the new sequence.
33. Click on "Add User" and add a "Physicist" user using a second email address that you have access to.
34. Logout.
35. Click on the link in the email sent to you to create your password.
36. Create your password, and login.
36. Navigate to the "configuration" page and verify that you can not see the "users" section.
37. Logout, and log back into the first account.
38. Navigate to "Configuration" and delete the new user.
39. Create a new machine, sequence, and phantom. Use a tolerance of 2.0 for the sequence.
40. Navigate to the home page and select "Upload Scan."
41. Select your new machine, sequence, and phantom, and choose `data/dicom/006_mri_603A_UVA_Axial_2ME2SRS5.zip` for the MRI Scan Files.
42. Submit the form and wait until the data is finished processing.
43. Click on "DICOM Overlay," and fill in the form with arbitrary info.
44. Verify that a zipfile is downloaded, and return to the machine-sequence detail page.
45. Click on "Raw Data," and verify that dicom.zip, institution.json, machine.json, phantom.json, raw_points.mat, sequence.json, and voxels.mat are present.
46. Click on "Executive Report" and "Full Report."
47. Increase the tolerance threshold to somewhere above the maximum distortion, save it, and hit the refresh button on the scan row.
48. Wait until the data is finished processing.
49. Verify that the new scan is marked as "passed."
50. Delete the new scan.
51. Navigate to "Account."
52. Edit your account info, and verify that it's updated.
53. Navigate to "/fake-server-error" and verify that the Server Error page is displayed.
54. Navigate to "/missing-page" and verify that that the 404 page is displayed.

[comment]: <> (TODO test filters on landing page and machine-sequence detail page)
