import matplotlib
# Garante que o Matplotlib funcione no Mac sem precisar de GUI
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

class DotaVisualizer:
    def __init__(self, model, feature_names):
        self.model = model
        self.feature_names = feature_names

    def plot_feature_importance(self, save_path='plots/impacto_meta_atual.png'):
        print("📊 Gerando gráfico de Impacto do Meta...")
        
        # 1. Extrair importâncias do XGBoost
        importances = self.model.feature_importances_
        
        # 2. Criar DataFrame de importâncias de forma robusta
        data = pd.DataFrame({
            'Indicador': self.feature_names,
            'Impacto': importances
        })

        # 3. Filtrar e ordenar apenas as top 20 para o gráfico não ficar poluído
        data = data.sort_values(by='Impacto', ascending=False).head(20)

        if data.empty:
            print("⚠️ Sem dados de importância suficientes para gerar o gráfico.")
            return

        # 4. Configurar estilo visual
        plt.figure(figsize=(14, 10))
        sns.set_theme(style="whitegrid", palette="dark")
        
        # 5. Criar gráfico de barras horizontal
        barplot = sns.barplot(
            x="Impacto", 
            y="Indicador", 
            data=data,
            hue="Indicador", # Necessário para o Seaborn aplicar a paleta
            legend=False,
            palette="viridis"
        )
        
        # 6. Customizar Labels (Sem emojis para evitar erro no Mac)
        plt.title('Dota Intelligence: Quais Fatores Decidem o Jogo?', fontsize=20, fontweight='bold', pad=25)
        plt.xlabel('Pontuação de Impacto (Ganho de Informação)', fontsize=15)
        plt.ylabel('', fontsize=1) 
        plt.xticks(fontsize=13)
        plt.yticks(fontsize=13)

        # 7. Adicionar os valores exatos nas barras
        for i, v in enumerate(data['Impacto']):
            barplot.text(v + 0.005, i, f'{v:.3f}', color='black', va='center', fontweight='bold', fontsize=11)

        # 8. Salvar e fechar
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"✅ Gráfico salvo com sucesso em: {save_path}")