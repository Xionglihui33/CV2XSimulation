import random
import json
from lib.utils import *
"""
Linux: pycrypto
Windows: pycryptodome
"""


def hash_0(str_obj):
    """
    提供H0()
    """
    return get_crc32("HASH0" + str(str_obj))


def hash_1(str_obj):
    """
    提供H1()
    """
    return get_crc32("HASH1" + str(str_obj))


def hash_2(str_obj):
    """
    提供H2()
    """
    return get_crc32("HASH2" + str(str_obj))


def hash_3(str_obj):
    """
    提供H3()
    """
    return get_crc32("HASH3" + str(str_obj))


def hash_5(str_obj):
    """
    提供H5()
    """
    return get_crc32("HASH5" + str(str_obj))


def get_K_amf(offset):
    """
    生成一个K_amf
    """
    return get_crc32("K_AMF" + str(offset))


def get_ID_obu_i(offset):
    """
    生成一个ID_OBU_i
    """
    return get_crc32("ID_OBU_I" + str(offset))


def get_ID_gl(offset):
    """
    生成一个ID_GL
    """
    return get_crc32("ID_GL" + str(offset))


def get_ID_amf(offset):
    """
    生成一个ID_AMF
    """
    return get_crc32("ID_AMF" + str(offset))


def get_K_i(r_i, ID_AMF, P, K_AMF, P_pub):
    """
    计算K_i
    """
    return r_i * hash_1(str(ID_AMF) + str(P) + str(K_AMF)) * (P * K_AMF + P_pub)


def get_alpha_i(ID_AMF, K_i, R_i):
    """
    计算α_i
    """
    return hash_0(str(ID_AMF) + str(K_i) + str(R_i))


def get_theta_i():
    """
    计算θ_i
    """
    return random.randint(1, 65535)


def get_c_i(alpha_i, theta_i):
    """
    计算c_i
    """
    return alpha_i + theta_i


def get_beta_i(theta_i):
    """
    计算β_i
    """
    return hash_3(str(theta_i))


def get_V_i(beta_i, msg, ID_OBU_i):
    """
    计算V_i
    """
    json_obj = dict()
    json_obj["Mi"] = msg
    json_obj["ID_OBU_I"] = ID_OBU_i
    return aes_encrypt(json.dumps(json_obj), beta_i)


def get_x_i_y_i_PK_i(P, ID_OBU_i, s):
    """
    得到x_i, y_i, PK_i
    """
    d_i = random.randint(1, s)
    t_i = random.randint(1, s)
    T_i = t_i * P
    D_i = d_i * P
    h0 = hash_0(ID_OBU_i + D_i + T_i)
    v_i = h0 * t_i + s
    PK_i = D_i + h0 * T_i
    h1 = hash_1(ID_OBU_i + PK_i)
    x_i = d_i * h1
    y_i = v_i * h1
    return x_i, y_i, PK_i


def get_w_i(x_i, y_i, V_i, r_i):
    """
    计算w_i
    """
    return (x_i + y_i) * V_i + r_i


def get_delta_i(c_i, R_i, V_i, w_i, R) -> json:
    """
    得到δ_i
    """
    delta_i_obj = dict()
    delta_i_obj["c_i"] = c_i
    delta_i_obj["R_i"] = R_i
    delta_i_obj["V_i"] = V_i
    delta_i_obj["w_i"] = w_i
    delta_i_obj["R"] = R
    return delta_i_obj


def get_qm_msg(delta_list, W):
    """
    得到签密消息
    """
    json_obj = dict()
    qm_list = list()
    for v in delta_list:
        qm_json_obj = dict()
        qm_json_obj["V_i"] = v["V_i"]
        qm_json_obj["R_i"] = v["R_i"]
        qm_json_obj["c_i"] = v["c_i"]
        qm_list.append(qm_json_obj)
    json_obj["qm_list"] = qm_list
    json_obj["W"] = W
    return json_obj


def get_SK_i(r_AMF, R_i):
    """
    计算SK_i
    """
    return hash_5(r_AMF * R_i)


def get_rsp_msg(msg, nonce, GK_lambda):
    """
    根据req_msg获取到rsp_msg
    """
    json_obj = {"nonce": nonce, "GK_lambda": GK_lambda}
    return json.dumps(json_obj)


def get_ID_OBU_i_V_i_map(qm_msg, ID_AMF, P, K_AMF, P_pub, prime_nums):
    """
    获取ID_OBU_i为key的map
    """
    # prime_nums 就是 nonce
    ID_OBU_i_V_i_map = dict()
    R = 0
    R_i_msg_map = dict()
    r_AMF = random.randint(1, 65535)
    N = 1
    GK = random.randint(10000, 20000)
    for prime in prime_nums:
        N *= prime
    Nonce_list = list()
    for prime in prime_nums:
        Nonce_list.append(N // prime)
    m_sum = 0
    for i, Nonce_i in enumerate(Nonce_list):
        m_sum += get_reverse(Nonce_i, prime_nums[i]) * Nonce_list[i]
    GK_lambda = GK * m_sum

    for i, qm in enumerate(qm_msg["qm_list"]):
        r_i = qm["R_i"] // P
        K_i = get_K_i(r_i, ID_AMF, P, K_AMF, P_pub)
        alpha_i = get_alpha_i(ID_AMF, K_i, qm["R_i"])
        theta_i = qm["c_i"] - alpha_i
        beta_i = get_beta_i(theta_i)
        json_obj = json.loads(aes_decrypt(qm["V_i"], beta_i))
        ID_OBU_i_V_i_map[json_obj["ID_OBU_I"]] = qm["V_i"]
        R += qm["R_i"]
        rsp_msg = get_rsp_msg(json_obj["Mi"], prime_nums[i], GK_lambda)
        SK_i = get_SK_i(r_AMF, qm["R_i"])
        # 发送出去的数据，根据R_i索引
        R_i_msg_map[qm["R_i"]] = aes_encrypt(rsp_msg, SK_i)
    return ID_OBU_i_V_i_map, R, R_i_msg_map, r_AMF, GK


def get_h_AMF(R, R_AMF):
    """
    计算h_AMF
    """
    return hash_0(str(R) + str(R_AMF) + "suss")


def get_X_AMF(r_AMF, x_AMF, y_AMF, h_AMF):
    """
    计算X_AMF
    """
    return r_AMF + (x_AMF + y_AMF) * h_AMF
