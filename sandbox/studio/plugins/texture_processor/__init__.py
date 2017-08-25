import appleseed as asr
import appleseed.studio as studio
from appleseed.studio import ui
from appleseed.studio.Qt import QtWidgets
from appleseed.textureconverter import *

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


def register():
    menu = ui.find_or_create_menu("Plugins")

    act = QtWidgets.QAction("Convert textures", menu)
    act.triggered.connect(convert_all_textures_to_tx)

    menu.addAction(act)


def convert_all_textures_to_tx():
    def _find_maketx():
        root_path = studio.get_root_path()
        maketx_path = os.path.join(root_path, 'bin', 'maketx')

        if os.path.exists(maketx_path):
            return maketx_path
        else:
            raise Exception('maketx binary is not found')

    project = studio.current_project()

    if project is None:
        raise Exception('No project is opened')

    scene = project.get_scene()
    textures = get_textures(scene)

    tx_converter = TextureConverter(_find_maketx())

    for texture in textures:
        if texture.get_model() != 'disk_texture_2d':
            continue

        texture_parameters = texture.get_parameters()

        texture_path = texture_parameters['filename']
        texture_full_path = get_full_path(texture_path, project)

        if texture_full_path.endswith('.tx'):
            logging.debug('Skipped conversion of {}'.format(texture_full_path))
            continue

        new_texture_full_path = tx_converter.convert(texture_full_path)

        if new_texture_full_path is None:
            logging.info('Skipped conversion of {}'.format(texture_full_path))
        else:
            new_texture_path = os.path.join(os.path.dirname(texture_path),
                                            os.path.basename(new_texture_full_path))

            texture_parameters['filename'] = new_texture_path
            texture.set_parameters(texture_parameters)
            studio.set_project_dirty()
            logging.info('{} converted to {}'.format(texture_path, new_texture_path))


def get_textures(container):
    assert isinstance(container, asr.BaseGroup)

    textures = list(container.textures())

    assemblies = container.assemblies()
    for key in assemblies:
        textures += get_textures(assemblies[key])

    return textures


def get_full_path(texture_path, project):
    if os.path.isabs(texture_path):
        return texture_path
    else:
        return project.qualify_path(texture_path)
