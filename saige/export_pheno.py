import hail as hl
import argparse
import os
import tempfile


def main(args):
    hl.init(master=f'local[{args.n_threads}]',
            log=hl.utils.timestamp_path(os.path.join(tempfile.gettempdir(), 'export_pheno'), suffix='.log'),
            default_reference='GRCh38')
    cov_ht = hl.read_table(args.covariates_path).select('sex', 'age', *['pc' + str(x) for x in range(1, args.num_pcs + 1)])
    cov_ht = cov_ht.annotate(age2=cov_ht.age ** 2, age_sex=cov_ht.age * cov_ht.sex, age2_sex=cov_ht.age ** 2 * cov_ht.sex)
    mt = hl.read_matrix_table(args.input_file)
    if args.data_type == 'icd':
        mt = mt.filter_cols(mt.icd_code == args.pheno)
        mt = mt.annotate_entries(**{field: hl.int(value) for field, value in mt.entry.items()})
    else:
        mt = mt.drop('both_sexes_pheno', 'females_pheno', 'males_pheno')
        coding = hl.int(args.coding) if args.data_type == 'categorical' else hl.str(args.coding)
        mt = mt.filter_cols((mt.pheno == hl.int(args.pheno)) & (mt.coding == coding))
        if args.data_type == 'categorical':
            mt = mt.annotate_entries(**{field: hl.int(value) for field, value in mt.entry.items()})
    ht = mt.entries().key_by('userId')
    ht = ht.annotate(**cov_ht[ht.key])
    ht.export(args.output_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--covariates_path', help='Path to covariates file', required=True)
    parser.add_argument('--input_file', help='Input phenotype file', required=True)
    parser.add_argument('--data_type', help='Data type', required=True, choices=('icd', 'continuous', 'categorical', 'biomarkers'))
    parser.add_argument('--pheno', help='Pheno to output', required=True)
    parser.add_argument('--coding', help='Coding for pheno', default='')
    parser.add_argument('--output_file', help='Output file', required=True)
    parser.add_argument('--n_threads', help='Number of PCs to use', type=int, default=20)
    parser.add_argument('--n_threads', help='Number of threads', type=int, default=8)
    args = parser.parse_args()

    main(args)