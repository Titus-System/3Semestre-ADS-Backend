from .models.limpador_de_tabela import LimpadorDeTabela
import http.client

# limpa_comex_stat.dataframe
def executar_limpador_ano(ano:int):
    tipos = ['exp', 'imp'] # + ['exp_mun', 'imp_mun']
    limpador = LimpadorDeTabela()
    resolved = True
    for tipo in tipos:
        try:
            gerar = limpador.gerar_dataframe(ano, tipo)
            if gerar:
                limpador.limpar_e_salvar_tabelas()
            else:
                print(f'tabela {limpador.nome_arquivo} já foi tratada.\n')
        except http.client.IncompleteRead as e:
            resolved = False
            print(f'Não foi possível acessar a tabela {limpador.nome_arquivo} por {e}')
            pass
    return resolved


def start():
    not_resolved = []
    for ano in range(2014, 2026):
        operation = executar_limpador_ano(ano)
        if not operation: not_resolved.append(ano)
    
    print('As operações não foram resolvidas para os anos:', not_resolved)


if __name__ == '__main__':
    start()