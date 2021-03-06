.. _notes:

Annotations
===========

Wonambi allows you to add annotations to your signal, such as sleep staging and signal quality (epochwise), highlighted events, cycle markers and bookmarks.

You must first create an Annotations File, by clicking on ``New Annotations``.

You will be asked to provide a rater name. Annotations Files are divided into separate raters. Use the ``Annotations`` -> ``Rater`` menu to create new raters and switch between them.

To load previously created annotations, click on ``Load Annotations``:

.. image:: images/notes_03_load.png

Import sleep staging from an external source
--------------------------------------------

Wonambi can import sleep staging from files generated by Alice, Compumedics, Domino, FASST, RemLogic or Sandman.

To import external sleep staging, click on ``Annotations`` -> ``Import staging``, and select the source program:

.. image:: images/notes_04_import_fasst.png

For Compumedics staging, you will be prompted to provide the staging start time.

For all sources but FASST, you will be asked to provide a rater name, under which to save the staging in the Annotations file. You may create a new rater or overwrite the staging in an existing one.

For FASST staging, you'll first be asked to load the ``.mat`` file containing the FASST sleep scores. Then you'll need to indicate where to save the annotations in ``.xml`` format.

If importation is successful, the converted sleep staging will appear in the ``Overview`` panel:

.. image:: images/notes_05_show_imported.png

For RemLogic staging, make sure you select the following options when exporting from RemLogic:

..images:: images/notes_21_remlogic_options.png

Stage sleep
-----------

You can also stage sleep within Wonambi. First, make sure you are lined up with an epoch. Make sure you are zoomed to the 30-s view with ``View`` -> ``Window length`` --> ``Set to 30.0``.

If you are not lined up with the epoch start, click on ``Navigation`` --> ``Line Up with Epoch``.

Now you can use the ``Annotations`` -> ``Score`` menu or the associated keyboard shortcuts to stage sleep per epoch. 
Alternatively, you can select a stage from the ``Stage Box``:

.. image:: images/notes_09_stage_box.png

The ``Stage Box`` always displays the stage of the current epoch (as long as you are lined up with one).

Wonambi provides two parallel sleep scoring tracks: one for sleep stages, the other for signal quality. 
The idea is to keep sleep annotation separate from signal annotation, so that signal quality does not affect physiological parameters like sleep efficiency and relative stage durations.

We recommend that you first stage sleep, disregarding signal quality 
(except of course when it is unintelligible, in which case you can mark it as ``Artefact``). 
Then, you can make a second pass only evaluating signal quality, using the ``o`` and ``p`` keys for ``Good`` and ``Poor`` signal, respectively.
Similarly to the ``Stage Box``, the ``Quality Box`` displays the quality of the current epoch, and can be used to change it:

.. image:: images/notes_10_quality_box.png

Epochs marked as ``Poor`` signal are excluded from ``Analysis``, such as spindle and slow wave detection.

Epochs staged as ``Artefact`` are automatically flagged as ``Poor`` signal.

You can view staging and signal quality summary parameters by clicking ``Summary`` in the ``Annotations`` panel.

Mark cycles
-----------

The stages of sleep are normally segregated into cycles (N1; N2; N3; then REM). After staging, you can segment the hypnogram into cycles for use in analysis.

To mark a cycle start, line yourself up with the first epoch of the cycle and click on ``Annotations`` -> ``Cycle`` -> ``Set cycle start``.

.. image:: images/notes_11_set_cycle_start.png

A cycle start marker will appear as a red square bracket on the ``Overview`` panel:

.. image:: images/notes_12_cycle_marker.png

To mark a cycle end, line yourself up with the first epoch after the end of the cycle. Here, you can either use ``Set cycle end`` or, if this epoch is the start of the next cycle, simply use ``Set cycle start`` again.

Repeat for each cycle, and make sure to mark the end of the last cycle with ``Set cycle end``. Omitting this will result in illegible cycle data.

.. image:: images/notes_13_all_cycle_markers.png

To remove a cycle marker, line yourself up with that epoch and click ``Annotations`` -> ``Cycle`` -> ``Remove cycle marker``.

You can clear all cycle markers in the rater profile with ``Annotations`` -> ``Cycle`` -> ``Clear cycle markers``.

Mark events
-----------

In addition to epoch annotation, Wonambi allows you to mark events of varying duration directly on the trace.

To mark an event on the trace, enter *event edit mode* by clicking on the ``Event Mode`` icon:

.. image:: images/notes_07_event_mode.png

Next, select an event type in the ``Event Type box``:

.. image:: images/notes_08_evt_type_box.png

You can create a new event type with ``Annotations`` -> ``Event`` --> ``New Event Type``.

Now, click and drag along a segment of the signal from the desired channel to create a new event:

.. image:: images/notes_14_mark_event.png

Events belong to the channel on which they were marked, and appear as a darker colour on that channel (this might not show up in the above image). The colours themselves are automatically generated from the event type label text. 

By default, the events are also highlighted on all other channels in a lighter colour. You can disable this option by toggling ``View`` -> ``Full-length markers``.

To delete an event, make sure you are in *event edit mode*, and click on it, so that it becomes highlighted in bright yellow:

.. image:: images/notes_15_highlight_event.png

Now press the ``Delete`` key. Note: The event will be removed from both the trace and the Annotation File.

Events are visible both highlighted on the trace and in table form in the ``Annotations`` panel, under ``Annotations``.

Double-click on an event in the table to jump to its position on the trace.

You can also delete an event from the table by clicking it and pressing the ``Delete`` button below the table.

Export sleep scores as csv
--------------------------

You can export the current sleep scores as ``.csv`` file to disk.
To do so, click on ``Annotations`` -> ``Export staging``:

.. image:: images/notes_06_export.png

then select the file where you want to store the sleep scores.

Export sleep statistics as csv
------------------------------

You can export some sleep statistics (such as Total Sleep Time, WASO, etc)  as ``.csv`` file to disk.
To do so, click on ``Analysis`` -> ``Sleep statistics``:

.. image:: images/analysis_02_statistics.png

then select the file where you want to store the sleep scores.

In addition, you need to specify at what time the lights went off (``Lights OUT``) and when the lights went on (``Lights ON``):

.. image:: images/analysis_02_timedialog.png
