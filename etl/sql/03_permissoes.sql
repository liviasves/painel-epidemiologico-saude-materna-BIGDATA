-- Permissões do usuário do dashboard (criado pelo Terraform: terraform/dashboard.tf)
-- Ele só consegue LER as views de indicadores e as dimensões usadas nos filtros.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'dashboard_leitura') THEN
        GRANT USAGE ON SCHEMA public TO dashboard_leitura;
        GRANT SELECT ON vw_ind_mortalidade, vw_ind_parto, vw_ind_causas,
                        dim_uf, dim_municipio, dim_raca_cor, dim_escolaridade, dim_faixa_etaria,
                        controle_carga
              TO dashboard_leitura;
        RAISE NOTICE 'Permissões de leitura concedidas a dashboard_leitura';
    ELSE
        RAISE NOTICE 'Usuário dashboard_leitura não existe: rode terraform apply antes';
    END IF;
END $$;
