.. include:: ../common.txt

.. _gv-bindings:

:fa:`keyboard` Key Bindings
===========================

Primary keyboard and mouse bindings that control the rendered scene.

.. tab-set::

    .. tab-item:: :fab:`linux` / :fab:`windows`

        .. table:: Bindings (Linux/Windows)
            :widths: auto

            +----------------------------------------+------------------------------------------------+--------------+
            | :fa:`keyboard` + :fa:`computer-mouse`  | Action                                         | Example      |
            +========================================+================================================+==============+
            | :guilabel:`f` (`Qt`_)                  | Focus and zoom to a point.                     | |fvcom-f|    |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`q`                          | Quit the rendering window.                     |              |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`r`                          | Reset the camera.                              |              |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`s`                          | Render scene using ``surface`` style.          | |fvcom-s|    |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`v` (`Qt`_)                  | Snap to `isometric camera`_ view.              |              |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`v` (`Trame`_)               | Render scene using ``points`` style.           | |fvcom-p|    |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`w`                          | Render scene using ``wireframe`` style.        | |fvcom-w|    |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`L-Click`                    | Rotate the rendered scene in 3-D.              | |fvcom-3d|   |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`Ctrl + L-Click`             | Rotate the rendered scene in 2-D (view plane). | |fvcom-2d|   |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`Shift + L-Click` or         | Pan the rendered scene.                        | |fvcom-pan|  |
            | :guilabel:`M-Click`                    |                                                |              |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`Mouse-Wheel` or             | Continuously zoom the rendering scene.         | |fvcom-zoom| |
            | :guilabel:`R-Click`:sup:`†`            |                                                |              |
            +----------------------------------------+------------------------------------------------+--------------+

        :guilabel:`†` - **not** `Trame`_


    .. tab-item:: :fab:`apple`

        .. table:: Bindings (Mac)
            :widths: auto

            +----------------------------------------+------------------------------------------------+--------------+
            | :fa:`keyboard` + :fa:`computer-mouse`  | Action                                         | Example      |
            +========================================+================================================+==============+
            | :guilabel:`f` (`Qt`_)                  | Focus and zoom to a point.                     | |fvcom-f|    |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`q`                          | Quit the rendering window.                     |              |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`r`                          | Reset the camera.                              |              |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`s`                          | Render scene using ``surface`` style.          | |fvcom-s|    |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`v` (`Qt`_)                  | Snap to `isometric camera`_ view.              |              |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`v` (`Trame`_)               | Render scene using ``points`` style.           | |fvcom-p|    |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`w`                          | Render scene using ``wireframe`` style.        | |fvcom-w|    |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`⌘-Click`                    | Rotate the rendered scene in 3-D.              | |fvcom-3d|   |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`Ctrl + Click`               | Rotate the rendered scene in 2-D (view plane). | |fvcom-2d|   |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`Shift + Click`              | Pan the rendered scene.                        | |fvcom-pan|  |
            +----------------------------------------+------------------------------------------------+--------------+
            | :guilabel:`Ctrl + Click`               | Continuously zoom the rendering scene.         | |fvcom-zoom| |
            +----------------------------------------+------------------------------------------------+--------------+


.. |fvcom-s| image::  ../_static/images/fvcom-surface.png
    :scale: 30%
    :align: middle

.. |fvcom-w| image:: ../_static/images/fvcom-wireframe.png
    :scale: 30%
    :align: middle

.. |fvcom-p| image:: ../_static/images/fvcom-points.png
    :scale: 30%
    :align: middle

.. |fvcom-f| image:: https://raw.githubusercontent.com/bjlittle/geovista-media/2024.07.0/media/docs/fvcom-f.gif
    :scale: 30%
    :align: middle
    :height: 480
    :width: 640

.. |fvcom-3d| image:: https://raw.githubusercontent.com/bjlittle/geovista-media/2024.07.0/media/docs/fvcom-rotate-3d.gif
    :scale: 30%
    :align: middle
    :height: 480
    :width: 640

.. |fvcom-2d| image:: https://raw.githubusercontent.com/bjlittle/geovista-media/2024.07.0/media/docs/fvcom-rotate-2d.gif
    :scale: 30%
    :align: middle
    :height: 480
    :width: 640

.. |fvcom-pan| image:: https://raw.githubusercontent.com/bjlittle/geovista-media/2024.07.0/media/docs/fvcom-pan.gif
    :scale: 30%
    :align: middle
    :height: 480
    :width: 640

.. |fvcom-zoom| image:: https://raw.githubusercontent.com/bjlittle/geovista-media/2024.07.0/media/docs/fvcom-zoom.gif
    :scale: 30%
    :align: middle
    :height: 480
    :width: 640


.. comment

    Page link URL resources in alphabetical order:


.. _isometric camera: https://docs.pyvista.org/version/stable/api/plotting/_autosummary/pyvista.Plotter.view_isometric.html
