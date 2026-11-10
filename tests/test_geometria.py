from va.geometria import desvio_do_clique, desvio_entre, escala_para, ponto_no_canvas


def test_escala_nao_amplia_print_pequeno():
    assert escala_para(100, 50, 760, 520) == 1.0


def test_escala_reduz_print_grande_para_caber_com_margem():
    # largura limita: (760 - 160) / 2000 = 0.3; altura daria 0.36
    assert escala_para(2000, 1000, 760, 520, margem=80) == 0.3


def test_clique_no_centro_da_desvio_zero():
    assert desvio_do_clique(380, 260, 760, 520, 1.0) == (0, 0)


def test_clique_fora_do_print_gera_desvio():
    assert desvio_do_clique(10, 260, 760, 520, 1.0) == (-370, 0)


def test_desvio_respeita_a_escala():
    assert desvio_do_clique(480, 260, 760, 520, 0.5) == (200, 0)


def test_ida_e_volta_entre_desvio_e_ponto():
    x, y = ponto_no_canvas(-30, 12, 760, 520, 0.5)
    assert desvio_do_clique(x, y, 760, 520, 0.5) == (-30, 12)


def test_desvio_entre_dois_cliques_na_tela():
    assert desvio_entre((100, 200), (130, 190)) == (30, -10)


def test_desvio_zero_quando_os_cliques_coincidem():
    assert desvio_entre((50, 50), (50, 50)) == (0, 0)
