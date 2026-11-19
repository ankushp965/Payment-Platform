module "eks" {
    source = "terraform-aws-modules/eks/aws"
    version = "~>20.0"

    cluster_name = var.eks_cluster_name
    cluster_version = "1.31"

    cluster_endpoint_public_access = true

    vpc_id = module.vpc.vpc_id
    subnet_ids = module.vpc.private_subnets
    control_plane_subnet_ids = module.vpc.private_subnets

    enable_cluster_creator_admin_permissions = true

    eks_managed_node_groups = {
        payment_nodes = {
            min_size = 1
            max_size = 3
            desired_size = 2

            instance_types = var.instance_types
            capacity_type = "SPOT"

            labels = {
                Environment = var.environment
                Project = var.project_name
            }

        }
    }
}