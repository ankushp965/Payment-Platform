variable "aws_region" {
  description = "AWS region for payment platform"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "payment-platform"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "eks_cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "payment-eks-cluster"
}

variable "instance_types" {
  description = "EKS worker node instance types"
  type        = list(string)
  default     = ["c7i-flex.large"]
} 