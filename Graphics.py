# # --- Graphics ---
# #
# # - General graphical functions
# #
# # --- --- --- ---


def scale(point, data):
    return [point[i] * data.zoom - data.viewPos[i] for i in range(2)]
