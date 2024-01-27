.. _experts:

For Experts: NERSC & KPNO
=========================

The Nightwatch monitor and webapp run daily at NERSC and KPNO. Here we detail
where and how to alter the behavior of these programs. These instructions are
intended for experts with access to the ``desi`` user at NERSC and the
``datasystems`` user at KPNO.

The NERSC scrontab
------------------

The Nightwatch monitor is run on Perlmutter by sourcing the nightwatch script:

.. code-block:: bash

  $CFS/desi/spectro/nightwatch/nersc/scron_nightwatch.sh

In general, Nightwatch should be running persistently as a result of being
sourced via ``scron`` as specified in the desi user's scrontab. There should be
at most one instance of nightwatch running at any time.

Modifying how nightwatch runs should be done by editing the above script. This
can only be done as the desi user. Log into ``perlmutter`` as the ``desi`` user using the `sshproxy service <https://docs.nersc.gov/connect/mfa/#sshproxy>`_:

.. code-block:: bash

  sshproxy.sh -c desi
  ssh -i $HOME/.ssh/desi desi@perlmutter-p1.nersc.gov

To see the scrontab entry for Nightwatch, run

.. code-block:: bash

  scrontab -l | grep scron_nightwatch

To monitor the scron job(s), run

.. code-block:: bash

  squeue -u desi -q workflow,cron -O Name:10,qos:10,JobID:10,State,EligibleTime,StartTime | grep scron_nw

.. note::

  All Nightwatch scron jobs are called ``scron_nw``; there should be at most
  two of these running on perlmutter.

To modify the Nightwatch script, follow these steps:

#. Suspend the scron job:

   a. Run ``scrontab -e``.

   b. Comment the entire block ending with the line ``source $CFS/desi/spectro/nightwatch/nersc/scron_nightwatch.sh``. To do this properly, insert the characters "# " at the start of each line in the scrontab block.

#. Stop Nightwatch cleanly:

   .. code-block:: bash

      cd $CFS/desi/spectro/nightwatch/nersc
      touch stop.nightwatch
      tail -f nightwatch.log

   Monitor the log file to see that Nightwatch has in fact stopped. Once it
   cleanly ends, remove the stopfile:

   .. code-block:: bash

      rm stop.nightwatch

#. Modify the Nightwatch script as needed. Its location is

   .. code-block::

      $CFS/desi/spectro/nightwatch/nersc/scron_nightwatch.sh

#. Resume the scron job by running ``scrontab -e`` and uncommenting the code block ending with ``source $CFS/desi/spectro/nightwatch/nersc/scron_nightwatch.sh``. The job will restart at the time indicated in the scrontab entry; it should be at 30 minutes past the hour.

