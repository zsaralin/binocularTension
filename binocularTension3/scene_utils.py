import pyglet.gl as gl
import pyrealsense2 as rs
import pyglet

def axes(size=1, width=1):
    """Draw 3D axes"""
    gl.glLineWidth(width)
    pyglet.graphics.draw(6, gl.GL_LINES,
                         ('v3f', (0, 0, 0, size, 0, 0,
                                  0, 0, 0, 0, size, 0,
                                  0, 0, 0, 0, 0, size)),
                         ('c3f', (1, 0, 0, 1, 0, 0,
                                  0, 1, 0, 0, 1, 0,
                                  0, 0, 1, 0, 0, 1
                                  ))
                         )

def frustum(intrinsics):
    """Draw camera's frustum"""
    w, h = intrinsics.width, intrinsics.height
    batch = pyglet.graphics.Batch()

    for d in range(1, 6, 2):
        def get_point(x, y):
            p = rs.rs2_deproject_pixel_to_point(intrinsics, [x, y], d)
            batch.add(2, gl.GL_LINES, None, ('v3f', [0, 0, 0] + p))
            return p

        top_left = get_point(0, 0)
        top_right = get_point(w, 0)
        bottom_right = get_point(w, h)
        bottom_left = get_point(0, h)

        batch.add(2, gl.GL_LINES, None, ('v3f', top_left + top_right))
        batch.add(2, gl.GL_LINES, None, ('v3f', top_right + bottom_right))
        batch.add(2, gl.GL_LINES, None, ('v3f', bottom_right + bottom_left))
        batch.add(2, gl.GL_LINES, None, ('v3f', bottom_left + top_left))

    batch.draw()

def grid(size=1, n=10, width=1):
    """Draw a grid on the xz plane"""
    gl.glLineWidth(width)
    s = size / float(n)
    s2 = 0.5 * size
    batch = pyglet.graphics.Batch()

    for i in range(0, n + 1):
        x = -s2 + i * s
        batch.add(2, gl.GL_LINES, None, ('v3f', (x, 0, -s2, x, 0, s2)))
    for i in range(0, n + 1):
        z = -s2 + i * s
        batch.add(2, gl.GL_LINES, None, ('v3f', (-s2, 0, z, s2, 0, z)))

    batch.draw()
