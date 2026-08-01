# Modelo conceitual

## Unidade central

A unidade central permanece a instituição ou infraestrutura audiovisual observada. A nova camada descreve a rede de dependências que conecta essa unidade a tecnologias, fornecedores, contratos, fluxos e serviços externos.

```text
instituição pública
  ├── utiliza → tecnologia
  ├── contrata/recebe → fornecedor
  ├── formaliza → contrato ou instrumento
  ├── envia/recebe → fluxo de dados
  ├── depende de → plataforma ou infraestrutura externa
  └── opera → sistema de IA ou automação
```

## Entidades

### Institution
Arquivo, cinemateca, emissora pública, agregador, fundação, órgão governamental ou organização híbrida.

### Technology
Sistema, software, padrão, protocolo, serviço de nuvem, mecanismo de busca, repositório, ferramenta analítica ou plataforma de distribuição.

### Provider
Pessoa jurídica pública, privada, sem fins lucrativos ou consórcio que fornece, mantém, integra ou opera tecnologia.

### InstitutionTechnologyRelation
Relação muitos-para-muitos entre instituição, tecnologia e, quando aplicável, fornecedor.

### ProcurementContract
Contrato, licitação, adjudicação, convênio ou outro instrumento que documenta aquisição ou prestação tecnológica.

### DataFlow
Movimento de dados entre origem e destino, com método, formato, frequência e finalidade.

### AISystem
Aplicação de IA ou automação associada a função concreta, estágio de implantação e evidência verificável.

### GovernanceEvidence
Documento ou página que sustenta afirmações sobre governança, privacidade, licenciamento, compartilhamento, transparência ou responsabilidade.

### InfrastructureRisk
Avaliação controlada de dependência, concentração, descontinuidade, interoperabilidade ou responsabilização pública.

### Evidence
Registro transversal que preserva URL, data, trecho, tipo de fonte, método de obtenção, confiança e status de validação.

## Camadas do stack

- infraestrutura física;
- nuvem e hospedagem;
- rede e CDN;
- banco de dados;
- gestão de repositório;
- metadados;
- APIs e interoperabilidade;
- busca e descoberta;
- autenticação;
- gestão de direitos;
- analytics;
- IA e automação;
- interface pública;
- distribuição externa.

## Regras de modelagem

- fornecedores, tecnologias e contratos são entidades separadas;
- uma instituição pode usar várias tecnologias e fornecedores;
- um fornecedor pode cumprir diferentes papéis;
- contratos não são inferidos apenas pela detecção técnica;
- ausência de sinal não equivale a ausência da tecnologia;
- cada relação substantiva deve apontar para pelo menos uma evidência;
- classificações de risco não devem ser produzidas diretamente pelo detector bruto;
- dados brutos, curados e longitudinais permanecem separados.